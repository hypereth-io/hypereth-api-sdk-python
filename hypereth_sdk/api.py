"""
HyperETH API client with HyperLiquid integration
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone

from .crypto import WalletSigner
from .hyperliquid.client import HyperLiquidClient
from .asterdex.client import AsterDexClient
from .http_client import HTTPClient
from .websocket_client import WebSocketClient
from .models import APIKey, APIKeyResponse
from .exceptions import ValidationError, APIError
from .constants import Exchange


class HyperETHClient:
    """
    Main client for HyperETH API with HyperLiquid integration

    This client provides methods for:
    - HyperETH API key management (register, list, delete)
    - HyperLiquid /info endpoint methods (via REST and WebSocket)
    - HyperLiquid /exchange endpoint methods (via REST and WebSocket)
    - WebSocket subscriptions for real-time data
    """

    def __init__(
        self,
        base_url: str = "https://api.hypereth.io",
        private_key: Optional[str] = None,
        timeout: int = 30,
        api_key: Optional[str] = None,
        environment: str = "testnet",
        ws_url: str = "wss://api.hypereth.io/ws"
    ):
        """
        Initialize HyperETH client

        Args:
            base_url: Base URL of the HyperETH API
            private_key: Private key for wallet operations (hex string, optional)
            timeout: HTTP request timeout in seconds
            api_key: Optional API key for x-api-key header
            environment: Target environment (testnet/mainnet)
            ws_url: WebSocket URL for real-time API
        """
        self.base_url = base_url
        self.environment = environment
        self.env_param = f"?env={environment}" if environment == "testnet" else ""

        # Initialize HTTP client
        self.http_client = HTTPClient(base_url, timeout, api_key)

        # Initialize WebSocket client
        self.ws_client = WebSocketClient(ws_url, environment, api_key)

        # Initialize wallet signer if private key provided
        self.wallet = WalletSigner(private_key) if private_key else None


        # Initialize sub-clients for each DEX
        # Derive HyperLiquid WebSocket URL from the main WebSocket URL
        hl_ws_url = ws_url.replace("/ws", "/v1/hl/ws") if "/v1/hl/ws" not in ws_url else ws_url

        self.hl = HyperLiquidClient(
            base_url=base_url + "/v1/hl" if not base_url.endswith("/v1/hl") else base_url,
            api_key=api_key,
            timeout=timeout,
            environment=environment,
            private_key=private_key,
            ws_url=hl_ws_url
        )

        # Derive AsterDex WebSocket URLs from the main WebSocket URL
        aster_perp_ws_url = ws_url.replace("/ws", "/v1/aster/perp/ws") if "/v1/aster" not in ws_url else ws_url
        aster_spot_ws_url = ws_url.replace("/ws", "/v1/aster/spot/ws") if "/v1/aster" not in ws_url else ws_url

        self.aster = AsterDexClient(
            base_url=base_url + "/v1/aster" if not base_url.endswith("/v1/aster") else base_url,
            hypereth_api_key=api_key,
            timeout=timeout,
            perp_ws_url=aster_perp_ws_url,
            spot_ws_url=aster_spot_ws_url
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Initialize WebSocket connection and fetch metadata."""
        await self.ws_client.connect()
        # Also connect HyperLiquid WebSocket if needed
        await self.hl.connect()
        # Fetch metadata on startup
        await self.hl.get_meta()

    async def disconnect(self):
        """Clean up connections."""
        await self.ws_client.disconnect()
        await self.hl.disconnect()
        # Disconnect AsterDex WebSocket if connected
        await self.aster.disconnect_ws()

    @property
    def wallet_address(self) -> str:
        """Get the wallet address"""
        if not self.wallet:
            raise ValidationError("No wallet initialized - private key required")
        return self.wallet.address

    def get_builder_fee_info(self) -> dict:
        """
        Get information needed to approve builder fee

        Returns:
            Dictionary with builder address and fee amount
        """
        from .hyperliquid.builder import HLBuilderInfo
        return HLBuilderInfo.get_approve_builder_fee_data()

    async def register_api_key(self) -> APIKeyResponse:
        """
        Register a new API key

        Before calling this method, ensure you have:
        1. Approved the builder fee using the approveBuilderFee function
        2. Your wallet is whitelisted (for initial version)

        Returns:
            APIKeyResponse with the new API key
        """
        # Generate nonce
        nonce = self.wallet.generate_nonce()

        # Sign registration message
        _, signature = self.wallet.sign_registration_message(nonce)

        # Prepare request data
        request_data = {
            "signature": signature if signature.startswith('0x') else f"0x{signature}",
            "nonce": nonce
        }

        # Make API request
        try:
            response_data = await self._make_async_request("post", "/v1/api_key/register", request_data)

            # Parse response
            api_key = None
            if response_data.get("api_key"):
                api_key = APIKey(
                    key=response_data["api_key"],
                    created_at=datetime.now(timezone.utc),
                    is_active=True
                )

            return APIKeyResponse(
                success=response_data.get("success", True),
                message=response_data.get("message", "API key registered successfully"),
                api_key=api_key
            )

        except Exception as e:
            return APIKeyResponse(
                success=False,
                message=f"Registration failed: {e}"
            )

    async def list_api_keys(self) -> APIKeyResponse:
        """
        List all API keys for this wallet

        Returns:
            APIKeyResponse with list of API keys
        """
        # Generate nonce
        nonce = self.wallet.generate_nonce()

        # Sign list message
        _, signature = self.wallet.sign_list_message(nonce)

        # Prepare request data
        request_data = {
            "signature": signature,
            "nonce": nonce
        }

        # Make API request
        try:
            response_data = await self._make_async_request("post", "/v1/api_key/list", request_data)

            # Parse response
            api_keys = []
            if response_data.get("api_keys"):
                for key_data in response_data["api_keys"]:
                    # Detailed key information
                    created_at = None
                    if key_data.get("created_at"):
                        try:
                            created_at = datetime.fromisoformat(key_data["created_at"])
                        except ValueError:
                            pass

                    last_used = None
                    if key_data.get("last_used"):
                        try:
                            last_used = datetime.fromisoformat(key_data["last_used"])
                        except ValueError:
                            pass

                    api_keys.append(APIKey(
                        key=key_data["api_key"],
                        created_at=created_at,
                        last_used=last_used,
                        is_active=key_data.get("is_active", True)
                    ))

            return APIKeyResponse(
                success=response_data.get("success", True),
                message=response_data.get("message", f"Found {len(api_keys)} API keys"),
                api_keys=api_keys
            )

        except Exception as e:
            return APIKeyResponse(
                success=False,
                message=f"Failed to list API keys: {e}"
            )

    async def delete_api_key(self, api_key: str) -> APIKeyResponse:
        """
        Delete an API key

        Args:
            api_key: The API key to delete

        Returns:
            APIKeyResponse indicating success or failure
        """
        if not api_key:
            raise ValidationError("API key is required")

        # Generate nonce
        nonce = self.wallet.generate_nonce()

        # Sign delete message
        _, signature = self.wallet.sign_delete_message(api_key, nonce)

        # Prepare request data
        request_data = {
            "api_key_to_delete": api_key,
            "signature": signature,
            "nonce": nonce
        }

        # Make API request
        try:
            response_data = await self._make_async_request("delete", "/v1/api_key", request_data)

            return APIKeyResponse(
                success=response_data.get("success", True),
                message=response_data.get("message", "API key deleted successfully")
            )

        except Exception as e:
            return APIKeyResponse(
                success=False,
                message=f"Failed to delete API key: {e}"
            )

    # =================================================================
    # TRADE INTENT (Generic for all DEXes)
    # =================================================================

    async def submit_trade_intent(self,
                                 exchange: Union[Exchange, str],
                                 **kwargs) -> Dict[str, Any]:
        """
        Submit a generic trade intent for any supported DEX

        Args:
            exchange: Exchange identifier (Exchange.HYPERLIQUID, Exchange.ASTERDEX, or string)
            **kwargs: Exchange-specific parameters
                For HyperLiquid:
                    - action: HyperLiquid action dictionary
                    - agent_wallet: Agent wallet address
                    - nonce: Nonce for the request
                For AsterDex:
                    - TODO.

        Returns:
            Dictionary with trade intent result
        """
        try:
            # Convert Exchange enum to string if needed
            if isinstance(exchange, Exchange):
                exchange_str = exchange.value
            else:
                exchange_str = exchange

            # Build payload based on exchange type
            if exchange_str == "hyperliquid" or exchange == Exchange.HYPERLIQUID:
                # HyperLiquid expects specific format
                if 'action' not in kwargs or 'agent_wallet' not in kwargs or 'nonce' not in kwargs:
                    raise ValidationError("HyperLiquid trade intent requires 'action', 'agent_wallet', and 'nonce'")

                payload = {
                    "hl_action": kwargs['action'],
                    "hl_agent_wallet": kwargs['agent_wallet'],
                    "nonce": kwargs['nonce']
                }
            elif exchange_str == "asterdex" or exchange == Exchange.ASTERDEX:
                # AsterDex specific payload format
                # TODO: Implement AsterDex payload format
                payload = kwargs
            else:
                # Generic format for other exchanges
                payload = kwargs

            response_data = await self._make_async_request(
                "post",
                "/v1/trade/intent",
                payload
            )
            return response_data
        except Exception as e:
            raise APIError(f"Failed to submit trade intent: {e}")

    async def submit_trade_intent_ws(self,
                                    exchange: Union[Exchange, str],
                                    **kwargs) -> Dict[str, Any]:
        """
        Submit a trade intent via WebSocket for any supported DEX

        Args:
            exchange: Exchange identifier (Exchange.HYPERLIQUID, Exchange.ASTERDEX, etc.)
            **kwargs: Exchange-specific parameters

        Returns:
            Dictionary with trade intent result
        """
        try:
            # Convert Exchange enum to string if needed
            if isinstance(exchange, Exchange):
                exchange_str = exchange.value
            else:
                exchange_str = exchange

            # Build payload based on exchange type
            if exchange_str == "hyperliquid" or exchange == Exchange.HYPERLIQUID:
                if 'action' not in kwargs or 'agent_wallet' not in kwargs or 'nonce' not in kwargs:
                    raise ValidationError("HyperLiquid trade intent requires 'action', 'agent_wallet', and 'nonce'")

                payload = {
                    "hl_action": kwargs['action'],
                    "hl_agent_wallet": kwargs['agent_wallet'],
                    "nonce": kwargs['nonce']
                }
            elif exchange_str == "asterdex" or exchange == Exchange.ASTERDEX:
                payload = kwargs
            else:
                payload = kwargs

            request = {
                "method": "post",
                "request": {
                    "type": "trade_intent",
                    "payload": payload
                }
            }
            response = await self.ws_client.send_request(request)
            return response.get("response", {}).get("payload", {})
        except Exception as e:
            raise APIError(f"Failed to submit trade intent via WS: {e}")



    # =================================================================
    # INTERNAL HELPER METHODS
    # =================================================================

    async def _make_async_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal method to make async HTTP requests using aiohttp session.

        Args:
            method: HTTP method (get, post, delete)
            endpoint: API endpoint
            data: Request data for POST/DELETE

        Returns:
            Response data
        """
        # Add testnet parameter if needed
        if self.environment == "testnet" and "?" not in endpoint:
            endpoint += "?env=testnet"

        # Use the HTTP client's async methods
        if method.upper() == "POST":
            return await self.http_client.post_async(endpoint, data)
        elif method.upper() == "DELETE":
            return await self.http_client.delete_async(endpoint, data)
        elif method.upper() == "GET":
            return await self.http_client.get_async(endpoint, data)
        else:
            raise APIError(f"Unsupported HTTP method: {method}")
