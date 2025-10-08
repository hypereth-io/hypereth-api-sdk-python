"""
HyperLiquid API client implementation
"""

import logging
from typing import Dict, Any, Optional
from ..http_client import HTTPClient
from ..websocket_client import WebSocketClient
from ..exceptions import APIError, ValidationError
from .utils import round_size, round_price
from .builder import HLBuilderInfo

logger = logging.getLogger(__name__)

# Import signing utilities
from hyperliquid.utils.signing import (
    sign_l1_action, get_timestamp_ms, sign_agent,
    float_to_wire, order_wires_to_order_action
)
import eth_account
from eth_account.signers.local import LocalAccount


class HyperLiquidClient:
    """
    Client for HyperLiquid-specific API methods
    """

    def __init__(
        self,
        base_url: str = "https://api.hypereth.io/v1/hl",
        api_key: Optional[str] = None,
        timeout: int = 30,
        environment: str = "testnet",
        private_key: Optional[str] = None,
        agent_address: Optional[str] = None,
        ws_url: str = "wss://api.hypereth.io/v1/hl/ws"
    ):
        """
        Initialize HyperLiquid client

        Args:
            base_url: Base URL for HyperLiquid API (defaults to HyperETH's HyperLiquid proxy)
            api_key: Optional API key for x-api-key header
            timeout: HTTP request timeout in seconds
            environment: Target environment (testnet/mainnet)
            private_key: Optional private key for user wallet (hex string)
            agent_address: Optional agent wallet address
            ws_url: WebSocket URL (defaults to wss://api.hypereth.io/v1/hl/ws)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.environment = environment
        self.env_param = f"?env={environment}" if environment == "testnet" else ""
        self.timeout = timeout

        # Initialize HTTP client with base_url
        self._http_client = None  # Lazy loaded

        # WebSocket client for HyperLiquid
        self.ws_client = WebSocketClient(ws_url, environment, api_key)

        # Asset metadata cache
        self.asset_metadata = {}
        self.sz_decimals = {}  # Cache for szDecimals per asset
        self.asset_indices = {}  # Cache for asset indices

        # Trading-specific attributes
        self.user_wallet = None
        self.agent_wallet = None
        self.agent_address = agent_address

        # Set user wallet if private key provided
        if private_key:
            self.set_user_wallet(private_key)

    @property
    def http_client(self):
        """Lazy-loaded HTTP client"""
        if self._http_client is None:
            self._require_api_key()
            self._http_client = HTTPClient(self.base_url, self.timeout, self.api_key)
        return self._http_client

    def set_api_key(self, api_key: str, ws_url: str = "wss://api.hypereth.io/v1/hl/ws"):
        """
        Set or update the API key

        Args:
            api_key: The API key to use for authenticated requests
            ws_url: WebSocket URL (defaults to wss://api.hypereth.io/v1/hl/ws)
        """
        self.api_key = api_key
        # Reset HTTP client to force recreation with new API key
        self._http_client = None
        # Update WebSocket client as well
        self.ws_client = WebSocketClient(ws_url, self.environment, api_key)

    def _require_api_key(self):
        """Validate that API key is available for authenticated operations"""
        if not self.api_key:
            raise ValidationError("API key is required for this operation")

    async def connect(self):
        """Initialize WebSocket connection"""
        await self.ws_client.connect()

    async def disconnect(self):
        """Clean up WebSocket connection"""
        await self.ws_client.disconnect()

    async def get_all_mids(self) -> Dict[str, Any]:
        """
        Get all mid prices (market prices) for assets via HyperLiquid /info endpoint.

        Returns:
            Dictionary with mid prices for all assets
        """
        try:
            data = await self._post_info_request({"type": "allMids"})
            return data
        except Exception as e:
            raise APIError(f"Error getting mids: {e}")

    async def get_meta(self) -> Dict[str, Any]:
        """
        Get metadata for all assets including size decimals via HyperLiquid /info endpoint.
        Updates the internal cache of szDecimals for each asset.

        Returns:
            Metadata for all assets
        """
        try:
            data = await self._post_info_request({"type": "meta"})

            # Cache szDecimals and indices for each asset
            if "universe" in data:
                for index, asset in enumerate(data["universe"]):
                    asset_name = asset.get("name")
                    if asset_name:
                        self.sz_decimals[asset_name] = asset.get("szDecimals", 0)
                        self.asset_indices[asset_name] = index

            self.asset_metadata = data
            return data
        except Exception as e:
            raise APIError(f"Error getting meta: {e}")

    async def get_market_price(self, asset: str = "ETH") -> float:
        """
        Get current market price for an asset.

        Args:
            asset: Asset name (e.g., "ETH", "BTC", "DOGE")

        Returns:
            Current market price or 0 if not found
        """
        mids = await self.get_all_mids()
        return float(mids.get(asset, 0))

    async def get_l2_book(self, coin: str) -> Dict[str, Any]:
        """
        Get Level 2 order book for a specific coin via HyperLiquid /info endpoint.

        Args:
            coin: Coin symbol (e.g., "ETH", "BTC")

        Returns:
            Order book data with bids and asks
        """
        try:
            data = await self._post_info_request({
                "type": "l2Book",
                "coin": coin
            })
            return data
        except Exception as e:
            raise APIError(f"Error getting L2 book: {e}")

    async def get_candle_snapshot(self, coin: str, interval: str, start_time: int, end_time: int) -> Dict[str, Any]:
        """
        Get historical candle data via HyperLiquid /info endpoint.

        Args:
            coin: Coin symbol (e.g., "ETH", "BTC")
            interval: Time interval (e.g., "5m", "1h")
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds

        Returns:
            Dictionary with candle data
        """
        try:
            data = await self._post_info_request({
                "type": "candleSnapshot",
                "req": {
                    "coin": coin,
                    "interval": interval,
                    "startTime": start_time,
                    "endTime": end_time
                }
            })
            return data
        except Exception as e:
            raise APIError(f"Error getting candle snapshot: {e}")

    async def get_user_open_orders(self, user: str) -> Dict[str, Any]:
        """
        Get open orders for a user via HyperLiquid /info endpoint.

        Args:
            user: User address (hex string)

        Returns:
            Dictionary with open orders
        """
        try:
            data = await self._post_info_request({
                "type": "openOrders",
                "user": user
            })
            return data
        except Exception as e:
            raise APIError(f"Error getting user open orders: {e}")

    async def get_user_fills(self, user: str) -> Dict[str, Any]:
        """
        Get user fills via HyperLiquid /info endpoint.

        Args:
            user: User address (hex string)

        Returns:
            Dictionary with user fills
        """
        try:
            data = await self._post_info_request({
                "type": "userFills",
                "user": user
            })
            return data
        except Exception as e:
            raise APIError(f"Error getting user fills: {e}")

    async def get_user_funding(self, user: str, start_time: int, end_time: Optional[int] = None) -> Dict[str, Any]:
        """
        Get user funding payments.

        Args:
            user: User address (hex string)
            start_time: Start timestamp in milliseconds
            end_time: Optional end timestamp in milliseconds

        Returns:
            Dictionary with funding data
        """
        try:
            req = {
                "type": "userFunding",
                "user": user,
                "startTime": start_time
            }
            if end_time:
                req["endTime"] = end_time

            data = await self._post_info_request(req)
            return data
        except Exception as e:
            raise APIError(f"Error getting user funding: {e}")

    async def get_user_rate_limits(self, user: str) -> Dict[str, Any]:
        """
        Get user rate limit information.

        Args:
            user: User address (hex string)

        Returns:
            Dictionary with rate limit data
        """
        try:
            data = await self._post_info_request({
                "type": "userRateLimit",
                "user": user
            })
            return data
        except Exception as e:
            raise APIError(f"Error getting user rate limits: {e}")

    async def get_order_status(self, user: str, oid: int) -> Dict[str, Any]:
        """
        Get status of a specific order.

        Args:
            user: User address (hex string)
            oid: Order ID

        Returns:
            Dictionary with order status
        """
        try:
            data = await self._post_info_request({
                "type": "orderStatus",
                "user": user,
                "oid": oid
            })
            return data
        except Exception as e:
            raise APIError(f"Error getting order status: {e}")

    async def get_funding_history(self, coin: str, start_time: int, end_time: Optional[int] = None) -> Dict[str, Any]:
        """
        Get funding rate history for a coin.

        Args:
            coin: Coin symbol (e.g., "ETH", "BTC")
            start_time: Start timestamp in milliseconds
            end_time: Optional end timestamp in milliseconds

        Returns:
            Dictionary with funding history
        """
        try:
            req = {
                "type": "fundingHistory",
                "coin": coin,
                "startTime": start_time
            }
            if end_time:
                req["endTime"] = end_time

            data = await self._post_info_request(req)
            return data
        except Exception as e:
            raise APIError(f"Error getting funding history: {e}")

    # WebSocket methods
    async def send_ws_info_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an /info request via WebSocket.

        Args:
            payload: Request payload for /info endpoint

        Returns:
            Response data
        """
        request = {
            "method": "post",
            "request": {
                "type": "info",
                "payload": payload
            }
        }
        response = await self.ws_client.send_request(request)
        return response.get("response", {}).get("payload", {})

    async def send_ws_exchange_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an /exchange request via WebSocket.

        Args:
            payload: Request payload for /exchange endpoint

        Returns:
            Response data
        """
        request = {
            "method": "post",
            "request": {
                "type": "action",
                "payload": payload
            }
        }
        response = await self.ws_client.send_request(request)
        return response.get("response", {}).get("payload", {})

    # WebSocket subscription methods
    async def subscribe_to_channel(self, channel: str, params: Optional[Dict] = None):
        """
        Subscribe to a HyperLiquid WebSocket channel for real-time updates.

        Args:
            channel: Channel name (e.g., "allMids", "orderUpdates", "trades")
            params: Optional parameters for the subscription (e.g., {"coin": "SOL"} for trades channel)
        """
        if not self.ws_client.websocket:
            raise APIError("WebSocket not connected")

        import json
        subscription = {
            "method": "subscribe",
            "subscription": {
                "type": channel
            }
        }

        if params:
            subscription["subscription"].update(params)

        await self.ws_client.websocket.send(json.dumps(subscription))
        logger.info(f"Subscribed to HyperLiquid channel: {channel}")

    async def unsubscribe_from_channel(self, channel: str, params: Optional[Dict] = None):
        """
        Unsubscribe from a HyperLiquid WebSocket channel.

        Args:
            channel: Channel name to unsubscribe from (e.g., "trades", "allMids")
            params: Optional parameters that must match the original subscription
                   (e.g., {"coin": "SOL"} for trades channel)
        """
        if not self.ws_client.websocket:
            raise APIError("WebSocket not connected")

        import json
        unsubscription = {
            "method": "unsubscribe",
            "subscription": {
                "type": channel
            }
        }

        if params:
            unsubscription["subscription"].update(params)

        await self.ws_client.websocket.send(json.dumps(unsubscription))
        logger.info(f"Unsubscribed from HyperLiquid channel: {channel}")

    # =================================================================
    # BUILDER METHODS
    # =================================================================

    def get_builder_fee_info(self) -> dict:
        """
        Get information needed to approve builder fee

        Returns:
            Dictionary with builder address and fee amount
        """
        return HLBuilderInfo.get_approve_builder_fee_data()

    # =================================================================
    # MANAGED AGENT WALLET METHODS
    # =================================================================
    async def register_agent_wallet(self, name: str) -> Dict[str, Any]:
        """
        Register a new managed agent wallet on HyperETH for HyperLiquid.

        Args:
            name: Name for the agent wallet

        Returns:
            Dictionary with agent wallet details
        """
        try:
            response_data = await self.http_client.post_async(
                "/agent_wallet/register",
                {"name": name}
            )
            return response_data
        except Exception as e:
            raise APIError(f"Failed to register agent wallet: {e}")

    async def list_agent_wallets(self) -> list:
        """
        List all agent wallets managed by HyperETH for this API key.

        Returns:
            List of agent wallets
        """
        try:
            response_data = await self.http_client.get_async("/agent_wallet")
            return response_data if isinstance(response_data, list) else []
        except Exception as e:
            raise APIError(f"Failed to list agent wallets: {e}")

    async def delete_agent_wallet(self, agent_wallet_address: str) -> Dict[str, Any]:
        """
        Remove a managed agent wallet from HyperETH. Note that this does not remove the agent wallet
        from Hyperliquid itself, you have to do it manually on their UI.

        Args:
            agent_wallet_address: The agent wallet address to delete

        Returns:
            Dictionary with deletion result
        """
        try:
            response_data = await self.http_client.delete_async(
                f"/agent_wallet/{agent_wallet_address}"
            )
            return response_data
        except Exception as e:
            raise APIError(f"Failed to delete agent wallet: {e}")

    # =================================================================
    # TRADING METHODS
    # =================================================================

    def create_agent_wallet(self):
        """
        Create a new agent wallet for trading.
        Note that this is used for direct trading, and is not managed by HyperETH.

        Returns:
            Dictionary with agent wallet info
        """
        try:
            self.agent_wallet = eth_account.Account.create()
            self.agent_address = self.agent_wallet.address

            return {
                "agent_address": self.agent_address,
                "agent_private_key": self.agent_wallet.key.hex()
            }
        except Exception as e:
            raise APIError(f"Failed to create agent wallet: {e}")

    def set_user_wallet(self, private_key: str):
        """
        Set the main user wallet from private key.
        This wallet will be used to approve the agent wallet.

        Args:
            private_key: User's private key (with or without 0x prefix)
        """
        try:
            if private_key.startswith('0x'):
                self.user_wallet: LocalAccount = eth_account.Account.from_key(private_key)
            else:
                self.user_wallet: LocalAccount = eth_account.Account.from_key('0x' + private_key)

            return {
                "user_address": self.user_wallet.address
            }
        except Exception as e:
            raise APIError(f"Failed to set user wallet: {e}")

    def set_agent_address(self, agent_address: str):
        """
        Set the agent wallet address.
        This is typically used when using a managed agent wallet from HyperETH.

        Args:
            agent_address: The agent wallet address (hex string)
        """
        self.agent_address = agent_address

    def round_size_for_asset(self, size: float, asset: str) -> float:
        """Round size for specific asset."""
        sz_decimals = self.sz_decimals.get(asset, 4)
        return round_size(size, sz_decimals)

    def round_price_for_asset(self, price: float, asset: str) -> float:
        """Round price for specific asset."""
        sz_decimals = self.sz_decimals.get(asset, 4)
        return round_price(price, sz_decimals, False)

    async def approve_agent(self, agent_name: Optional[str] = "HyperETHBot") -> bool:
        """
        Approve agent wallet for trading using the main user wallet.
        Must be called before placing orders.
        """
        if not self.user_wallet:
            raise ValidationError("User wallet not set. Call set_user_wallet() first.")
        if not self.agent_address:
            raise ValidationError("Agent wallet not created. Call create_agent_wallet() first.")

        try:
            is_mainnet = self.environment == "mainnet"
            nonce = get_timestamp_ms()

            action = {
                "type": "approveAgent",
                "agentAddress": self.agent_address.lower(),
                "agentName": agent_name,
                "nonce": nonce
            }

            signature = sign_agent(self.user_wallet, action, is_mainnet)

            payload = {
                "action": action,
                "nonce": nonce,
                "signature": signature,
                "vaultAddress": None,
                "expiresAfter": None
            }

            result = await self._post_exchange_request(payload)

            if result.get("status") == "ok":
                return True
            else:
                raise APIError(f"Agent approval failed: {result}")

        except Exception as e:
            raise APIError(f"Agent approval error: {e}")

    def create_order_signature(self, order_action: dict, nonce: int) -> dict:
        """Create L1 signature for order using agent wallet."""
        if not self.agent_wallet:
            raise ValidationError("Agent wallet not created. Call create_agent_wallet() first.")

        try:
            is_mainnet = self.environment == "mainnet"
            signature = sign_l1_action(
                self.agent_wallet,
                order_action,
                None,
                nonce,
                None,
                is_mainnet
            )
            return signature
        except Exception as e:
            raise APIError(f"Order signing failed: {e}")

    def create_order_wire(self, asset_index: int, is_buy: bool, price: float, size: float) -> dict:
        """Create order wire format."""
        return {
            "a": asset_index,
            "b": is_buy,
            "p": float_to_wire(price),
            "s": float_to_wire(size),
            "r": False,
            "t": {"limit": {"tif": "Gtc"}}
        }

    def create_order_action(self, order_wires: list) -> dict:
        """Create order action."""
        action = order_wires_to_order_action(order_wires)
        action["grouping"] = "na"
        return action

    async def place_order_rest(self, price: str, size: str, is_buy: bool, asset: str = "ETH",
                              use_market_offset: bool = False, market_offset_pct: float = 0.10) -> dict:
        """Place order via REST API."""
        if not self.agent_wallet:
            raise ValidationError("Agent wallet not created. Call create_agent_wallet() first.")

        try:
            nonce = get_timestamp_ms()

            # Get market price and calculate final price/size
            market_price = await self.get_market_price(asset)
            if market_price <= 0:
                raise APIError(f"Could not get {asset} price")

            if use_market_offset:
                if is_buy:
                    calculated_price = market_price * (1 - market_offset_pct)
                else:
                    calculated_price = market_price * (1 + market_offset_pct)
                final_price = self.round_price_for_asset(calculated_price, asset)
            else:
                final_price = self.round_price_for_asset(float(price), asset)

            final_size = self.round_size_for_asset(float(size), asset)

            # Validations
            order_value = final_price * final_size
            if order_value < 10:
                min_size = 11 / final_price
                final_size = self.round_size_for_asset(min_size, asset)

            if asset == "ETH" and final_size < 0.01:
                final_size = 0.01
            elif asset == "DOGE":
                final_size = round(final_size)
                if final_size < 1:
                    final_size = 1

            asset_index = self.asset_indices.get(asset, -1)
            if asset_index == -1:
                raise APIError(f"Unknown asset: {asset}")

            # Create and send order
            order_wire = self.create_order_wire(asset_index, is_buy, final_price, final_size)
            action_data = self.create_order_action([order_wire])
            signature = self.create_order_signature(action_data, nonce)

            order_payload = {
                "action": action_data,
                "nonce": nonce,
                "signature": signature,
                "vaultAddress": None,
                "expiresAfter": None
            }

            result = await self._post_exchange_request(order_payload)
            return result

        except Exception as e:
            raise APIError(f"REST order failed: {e}")

    async def place_order_ws(self, price: str, size: str, is_buy: bool, asset: str = "ETH",
                            use_market_offset: bool = False, market_offset_pct: float = 0.10) -> dict:
        """Place order via WebSocket."""
        if not self.agent_wallet:
            raise ValidationError("Agent wallet not created. Call create_agent_wallet() first.")

        try:
            nonce = get_timestamp_ms()

            # Same price/size logic as REST
            market_price = await self.get_market_price(asset)
            if market_price <= 0:
                raise APIError(f"Could not get {asset} price")

            if use_market_offset:
                if is_buy:
                    calculated_price = market_price * (1 - market_offset_pct)
                else:
                    calculated_price = market_price * (1 + market_offset_pct)
                final_price = self.round_price_for_asset(calculated_price, asset)
            else:
                final_price = self.round_price_for_asset(float(price), asset)

            final_size = self.round_size_for_asset(float(size), asset)

            order_value = final_price * final_size
            if order_value < 10:
                min_size = 11 / final_price
                final_size = self.round_size_for_asset(min_size, asset)

            if asset == "ETH" and final_size < 0.01:
                final_size = 0.01
            elif asset == "DOGE":
                final_size = round(final_size)
                if final_size < 1:
                    final_size = 1

            asset_index = self.asset_indices.get(asset, -1)
            if asset_index == -1:
                raise APIError(f"Unknown asset: {asset}")

            # Create and send WebSocket order
            order_wire = self.create_order_wire(asset_index, is_buy, final_price, final_size)
            action_data = self.create_order_action([order_wire])
            signature = self.create_order_signature(action_data, nonce)

            ws_request = {
                "method": "post",
                "request": {
                    "type": "action",
                    "payload": {
                        "action": action_data,
                        "nonce": nonce,
                        "signature": signature,
                        "vaultAddress": None,
                        "expiresAfter": None
                    }
                }
            }

            response = await self.ws_client.send_request(ws_request)
            return response

        except Exception as e:
            raise APIError(f"WebSocket order failed: {e}")

    async def cancel_order_rest(self, order_id: int, asset_index: int) -> dict:
        """Cancel order via REST API."""
        if not self.agent_wallet:
            raise ValidationError("Agent wallet not created. Call create_agent_wallet() first.")

        try:
            nonce = get_timestamp_ms()

            action_data = {
                "type": "cancel",
                "cancels": [{
                    "a": asset_index,
                    "o": order_id
                }]
            }

            signature = self.create_order_signature(action_data, nonce)

            cancel_payload = {
                "action": action_data,
                "nonce": nonce,
                "signature": signature
            }

            result = await self._post_exchange_request(cancel_payload)
            return result

        except Exception as e:
            raise APIError(f"REST cancel failed: {e}")

    async def cancel_order_ws(self, order_id: int, asset_index: int) -> dict:
        """Cancel order via WebSocket."""
        if not self.agent_wallet:
            raise ValidationError("Agent wallet not created. Call create_agent_wallet() first.")

        try:
            nonce = get_timestamp_ms()

            action_data = {
                "type": "cancel",
                "cancels": [{
                    "a": asset_index,
                    "o": order_id
                }]
            }

            signature = self.create_order_signature(action_data, nonce)

            ws_request = {
                "method": "post",
                "request": {
                    "type": "action",
                    "payload": {
                        "action": action_data,
                        "nonce": nonce,
                        "signature": signature
                    }
                }
            }

            response = await self.ws_client.send_request(ws_request)
            return response

        except Exception as e:
            raise APIError(f"WebSocket cancel failed: {e}")

    # =================================================================
    # INTERNAL HELPER METHODS
    # =================================================================

    async def _post_info_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to send POST request to HyperLiquid /info endpoint.

        Args:
            payload: Request payload

        Returns:
            Response data
        """
        try:
            response = await self.http_client.post_async(
                f"/info{self.env_param}",
                payload
            )
            return response
        except Exception as e:
            raise APIError(f"Info request failed: {e}")

    async def _post_exchange_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to send POST request to HyperLiquid /exchange endpoint.

        Args:
            payload: Request payload

        Returns:
            Response data
        """
        try:
            response = await self.http_client.post_async(
                f"/exchange{self.env_param}",
                payload
            )
            return response
        except Exception as e:
            raise APIError(f"Exchange request failed: {e}")