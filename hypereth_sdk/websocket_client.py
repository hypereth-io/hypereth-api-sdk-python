"""
WebSocket client for real-time communication with HyperETH API
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import websockets
from websockets.exceptions import ConnectionClosed

from .exceptions import APIError

logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    WebSocket client for HyperETH API.

    Handles:
    - WebSocket connections with auto-reconnect
    - Message routing and request/response correlation
    - Subscription management
    - Real-time data streaming
    """

    def __init__(
        self,
        ws_url: str = "wss://api.hypereth.io/v1/hl/ws",
        environment: str = "testnet",
        api_key: Optional[str] = None
    ):
        """
        Initialize WebSocket client.

        Args:
            ws_url: WebSocket URL
            environment: Target environment (testnet/mainnet, or empty string for no env param)
            api_key: Optional API key for x-api-key header
        """
        # Only add environment parameter if not empty (for AsterDex compatibility)
        self.ws_url = f"{ws_url}?env={environment}" if environment else ws_url
        self.environment = environment
        self.api_key = api_key

        # Connection management
        self.websocket = None
        self.running = False

        # Request tracking
        self.request_counter = 0
        self.pending_requests: Dict[int, asyncio.Future] = {}

    async def connect(self):
        """Initialize WebSocket connection."""
        try:
            logger.info(f"Connecting to WebSocket: {self.ws_url}")

            # Prepare connection kwargs
            connect_kwargs = {
                "ping_interval": 20,
                "ping_timeout": 10,
                "close_timeout": 10
            }

            # Add headers if API key is provided (use additional_headers for websockets 15.0.1+)
            if self.api_key:
                connect_kwargs["additional_headers"] = {'x-api-key': self.api_key}

            self.websocket = await websockets.connect(
                self.ws_url,
                **connect_kwargs
            )
            self.running = True
            logger.info("Successfully connected to WebSocket")

            # Start message handler
            asyncio.create_task(self._message_handler())

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise APIError(f"WebSocket connection failed: {e}")

    async def disconnect(self):
        """Clean up WebSocket connection."""
        self.running = False

        if self.websocket:
            await self.websocket.close()

        logger.info("WebSocket connection closed")

    async def _message_handler(self):
        """Handle incoming WebSocket messages."""
        try:
            while self.running and self.websocket:
                try:
                    message = await self.websocket.recv()
                    await self._process_message(message)
                except ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error handling message: {e}")

        except Exception as e:
            logger.error(f"Message handler error: {e}")
        finally:
            # Complete pending requests with error
            for request_id, future in self.pending_requests.items():
                if not future.done():
                    future.set_exception(Exception("Connection closed"))
            self.pending_requests.clear()

    async def _process_message(self, message: str):
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            logger.debug(f"Received WS message: {data}")

            # Handle POST method responses
            if data.get("channel") == "post":
                response_data = data.get("data", {})
                request_id = response_data.get("id")

                # Log request_id for POST responses (it's at the root level)
                ws_request_id = data.get("request_id")
                if ws_request_id:
                    logger.debug(f"WebSocket POST Response request_id: {ws_request_id}")
                else:
                    logger.debug("WebSocket POST Response: no request_id field found")

                if request_id in self.pending_requests:
                    future = self.pending_requests.pop(request_id)
                    if not future.done():
                        future.set_result(response_data)
                else:
                    logger.warning(f"Received response for unknown request ID: {request_id}")

            # Handle order updates
            elif data.get("channel") == "orderUpdates":
                order_data = data.get("data", [])
                for order_update in order_data:
                    order_info = order_update.get("order", {})
                    status = order_update.get("status", "unknown")
                    oid = order_info.get("oid", "unknown")
                    logger.info(f"Order update - ID: {oid}, Status: {status}")

            # Handle subscription confirmation responses
            elif data.get("channel") == "subscriptionResponse":
                # Log request_id for subscription responses
                sub_request_id = data.get("request_id")
                if sub_request_id:
                    logger.debug(f"WebSocket subscriptionResponse request_id: {sub_request_id}")
                else:
                    logger.debug("WebSocket subscriptionResponse: no request_id field found")

                subscription_data = data.get("data", {})
                method = subscription_data.get("method", "unknown")
                sub_type = subscription_data.get("subscription", {}).get("type", "unknown")
                logger.info(f"Subscription {method} confirmed for type: {sub_type}")

            # Handle subscription updates (data feeds)
            elif "channel" in data:
                channel = data.get("channel")
                if channel == "allMids":
                    mids_data = data['data']['mids']
                    # Only show ETH price to keep output clean
                    if "ETH" in mids_data:
                        logger.info(f"AllMids update - ETH: ${mids_data['ETH']}")
                else:
                    logger.info(f"Received subscription update for channel: {channel}")
            else:
                # Print the entire message raw for types that are not predefined.
                logger.info(f"Received WS message: {data}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WS JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing WS message: {e}")

    async def send_request(self, request: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """
        Send a WebSocket request and wait for response.

        Args:
            request: Request payload
            timeout: Request timeout in seconds

        Returns:
            Response data
        """
        if not self.websocket or not self.running:
            raise APIError("WebSocket not connected")

        # Generate unique request ID
        self.request_counter += 1
        request_id = self.request_counter

        # Add ID to request if not present
        if "id" not in request:
            request["id"] = request_id

        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future

        try:
            # Send request
            await self.websocket.send(json.dumps(request))
            logger.debug(f"Sent WS request: {request}")

            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)

            # Check for error response
            if response.get("response", {}).get("type") == "error":
                error_msg = response.get("response", {}).get("payload", "Unknown error")
                raise APIError(f"API Error: {error_msg}")

            return response

        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise APIError(f"Request {request_id} timed out")
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            raise
