"""
AsterDex API client implementation
"""

import hmac
import hashlib
import time
from typing import Dict, Any, Optional, Union
from urllib.parse import urlencode
from ..http_client import HTTPClient
from ..websocket_client import WebSocketClient
from ..exceptions import APIError, ValidationError


class AsterDexClient:
    """
    Client for interacting with AsterDex APIs

    Supports both spot and perpetual (perp) trading on AsterDex.
    """

    def __init__(
        self,
        base_url: str = "https://api.hypereth.io/v1/aster",
        hypereth_api_key: Optional[str] = None,  # Optional for HyperETH proxy
        asterdex_api_key: Optional[str] = None,
        asterdex_api_secret: Optional[str] = None,
        timeout: int = 30,
        perp_ws_url: str = "wss://api.hypereth.io/v1/aster/perp/ws",
        spot_ws_url: str = "wss://api.hypereth.io/v1/aster/spot/ws"
    ):
        """
        Initialize AsterDex client

        Args:
            base_url: Base URL for AsterDex API (defaults to HyperETH's AsterDex proxy)
            hypereth_api_key: Optional HyperETH API key for x-api-key header (required for authenticated endpoints)
            asterdex_api_key: Optional AsterDex API key for SIGNED endpoints
            asterdex_api_secret: Optional AsterDex API secret for SIGNED endpoints (HMAC SHA256)
            timeout: HTTP request timeout in seconds
            perp_ws_url: WebSocket URL for perpetual markets (defaults to wss://api.hypereth.io/v1/aster/perp/ws)
            spot_ws_url: WebSocket URL for spot markets (defaults to wss://api.hypereth.io/v1/aster/spot/ws)
        """
        self.base_url = base_url
        self.hypereth_api_key = hypereth_api_key
        self.asterdex_api_key = asterdex_api_key
        self.asterdex_api_secret = asterdex_api_secret
        self.timeout = timeout
        # Initialize HTTP client with base_url
        self._http_client = None  # Lazy loaded

        # Store WebSocket URLs
        self.perp_ws_url = perp_ws_url
        self.spot_ws_url = spot_ws_url

        # WebSocket clients for spot and perp
        self.perp_ws_client = None
        self.spot_ws_client = None
        self._next_subscription_id = 1  # For tracking subscription IDs

    @property
    def http_client(self):
        """Lazy-loaded HTTP client"""
        if self._http_client is None:
            self._require_api_key()
            self._http_client = HTTPClient(self.base_url, self.timeout, self.hypereth_api_key)
        return self._http_client

    def set_api_key(self, api_key: str):
        """
        Set or update the HyperETH API key
        
        Args:
            api_key: The HyperETH API key to use for authenticated requests
        """
        self.hypereth_api_key = api_key
        # Reset HTTP client to force recreation with new API key
        self._http_client = None

    def _require_api_key(self):
        """Validate that HyperETH API key is available for authenticated operations"""
        if not self.hypereth_api_key:
            raise ValidationError("HyperETH API key is required for this operation")

    async def connect_perp_ws(self):
        """Connect to AsterDex perpetual WebSocket"""
        self._require_api_key()
        # AsterDex doesn't use environment parameter, pass empty string
        self.perp_ws_client = WebSocketClient(self.perp_ws_url, environment="", api_key=self.hypereth_api_key)
        await self.perp_ws_client.connect()

    async def connect_spot_ws(self):
        """Connect to AsterDex spot WebSocket"""
        self._require_api_key()
        # AsterDex doesn't use environment parameter, pass empty string
        self.spot_ws_client = WebSocketClient(self.spot_ws_url, environment="", api_key=self.hypereth_api_key)
        await self.spot_ws_client.connect()

    async def disconnect_ws(self):
        """Disconnect all WebSocket connections"""
        if self.perp_ws_client:
            await self.perp_ws_client.disconnect()
        if self.spot_ws_client:
            await self.spot_ws_client.disconnect()

    # =================================================================
    # SIGNATURE GENERATION FOR SIGNED ENDPOINTS
    # =================================================================

    def _generate_signature(self, params: Dict[str, Any], request_body: Optional[str] = None) -> str:
        """
        Generate signature for SIGNED endpoints (stub for now)

        Args:
            params: Query parameters as dictionary
            request_body: Optional request body string

        Returns:
            Signature string

        TODO: Implement proper signature generation:
        - v1 endpoints: HMAC SHA256 with asterdex_api_secret
        - v3 endpoints: Agent wallet signing
        """
        # Stub implementation - to be filled in later
        return "stub_signature"

    # =================================================================
    # GENERIC API REQUEST METHODS
    # =================================================================

    async def request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        signed: bool = False,
        api_type: str = "fapi"  # 'fapi' for futures, 'api' for spot
    ) -> Dict[str, Any]:
        """
        Generic request method for AsterDex API

        Args:
            endpoint: API endpoint path (e.g., "v1/exchangeInfo" or "v3/order")
            method: HTTP method (GET, POST, PUT, DELETE)
            params: Query parameters
            data: Request body data (for POST, PUT, DELETE)
            signed: Whether this is a SIGNED endpoint requiring signature
            api_type: API type - 'fapi' for futures, 'api' for spot

        Returns:
            Response data from the API
        """
        # Build full endpoint path
        full_endpoint = f"/{api_type}/{endpoint.lstrip('/')}"

        # Initialize params if None
        if params is None:
            params = {}

        # Handle signature for SIGNED endpoints
        if signed:
            # Add timestamp if not present
            if 'timestamp' not in params:
                params['timestamp'] = int(time.time() * 1000)

            # Generate signature
            request_body = urlencode(data) if data else None
            signature = self._generate_signature(params, request_body)
            params['signature'] = signature

        # Add query parameters to URL
        if params:
            query_string = urlencode(params)
            full_endpoint = f"{full_endpoint}?{query_string}"

        try:
            method = method.upper()
            if method == "GET":
                response = await self.http_client.get_async(full_endpoint)
            elif method == "POST":
                response = await self.http_client.post_async(full_endpoint, data)
            elif method == "PUT":
                # For PUT requests, we'll use POST with a special header or parameter
                # TODO: Add proper PUT support to HTTPClient
                response = await self.http_client.post_async(full_endpoint, data)
            elif method == "DELETE":
                # For DELETE requests, similar approach
                # TODO: Add proper DELETE support to HTTPClient
                response = await self.http_client.post_async(full_endpoint, data)
            else:
                raise ValidationError(f"Unsupported HTTP method: {method}")

            return response
        except Exception as e:
            raise APIError(f"AsterDex request failed: {e}")

    # Convenience methods for different HTTP methods and API types
    async def fapi_get(self, endpoint: str, params: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """Convenience method for futures GET requests"""
        return await self.request(endpoint, "GET", params=params, signed=signed, api_type="fapi")

    async def fapi_post(self, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """Convenience method for futures POST requests"""
        return await self.request(endpoint, "POST", params=params, data=data, signed=signed, api_type="fapi")

    async def fapi_put(self, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """Convenience method for futures PUT requests"""
        return await self.request(endpoint, "PUT", params=params, data=data, signed=signed, api_type="fapi")

    async def fapi_delete(self, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """Convenience method for futures DELETE requests"""
        return await self.request(endpoint, "DELETE", params=params, data=data, signed=signed, api_type="fapi")

    async def api_get(self, endpoint: str, params: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """Convenience method for spot GET requests"""
        return await self.request(endpoint, "GET", params=params, signed=signed, api_type="api")

    async def api_post(self, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """Convenience method for spot POST requests"""
        return await self.request(endpoint, "POST", params=params, data=data, signed=signed, api_type="api")


    # =================================================================
    # WEBSOCKET SUBSCRIPTION METHODS
    # =================================================================

    async def subscribe_perp_streams(self, streams: list):
        """
        Subscribe to perpetual WebSocket streams using AsterDex format

        Args:
            streams: List of stream names (e.g., ["btcusdt@aggTrade", "btcusdt@depth"])
        """
        if not self.perp_ws_client:
            await self.connect_perp_ws()

        import json
        subscription = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": self._next_subscription_id
        }
        self._next_subscription_id += 1

        await self.perp_ws_client.websocket.send(json.dumps(subscription))

    async def unsubscribe_perp_streams(self, streams: list):
        """
        Unsubscribe from perpetual WebSocket streams

        Args:
            streams: List of stream names to unsubscribe from
        """
        if not self.perp_ws_client or not self.perp_ws_client.websocket:
            return

        import json
        unsubscription = {
            "method": "UNSUBSCRIBE",
            "params": streams,
            "id": self._next_subscription_id
        }
        self._next_subscription_id += 1

        await self.perp_ws_client.websocket.send(json.dumps(unsubscription))

    async def subscribe_spot_streams(self, streams: list):
        """
        Subscribe to spot WebSocket streams using AsterDex format

        Args:
            streams: List of stream names (e.g., ["btcusdt@trade", "btcusdt@depth"])
        """
        if not self.spot_ws_client:
            await self.connect_spot_ws()

        import json
        subscription = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": self._next_subscription_id
        }
        self._next_subscription_id += 1

        await self.spot_ws_client.websocket.send(json.dumps(subscription))

    async def unsubscribe_spot_streams(self, streams: list):
        """
        Unsubscribe from spot WebSocket streams

        Args:
            streams: List of stream names to unsubscribe from
        """
        if not self.spot_ws_client or not self.spot_ws_client.websocket:
            return

        import json
        unsubscription = {
            "method": "UNSUBSCRIBE",
            "params": streams,
            "id": self._next_subscription_id
        }
        self._next_subscription_id += 1

        await self.spot_ws_client.websocket.send(json.dumps(unsubscription))