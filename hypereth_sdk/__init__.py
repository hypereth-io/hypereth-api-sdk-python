"""
HyperETH API SDK

A Python SDK for interacting with HyperETH API and HyperLiquid integration.
"""

from .api import HyperETHClient
from .hyperliquid import round_size, round_price
from .exceptions import HyperETHError, AuthenticationError, APIError, ValidationError, SigningError
from .models import APIKey, APIKeyResponse
from .crypto import WalletSigner
from .hyperliquid.builder import HLBuilderInfo
from .websocket_client import WebSocketClient
from .http_client import HTTPClient
from .constants import Exchange
from .asterdex import AsterDexClient

__version__ = "0.1.0"
__all__ = [
    "HyperETHClient",
    "HyperETHError",
    "AuthenticationError",
    "APIError",
    "ValidationError",
    "SigningError",
    "APIKey",
    "APIKeyResponse",
    "WalletSigner",
    "HLBuilderInfo",
    "WebSocketClient",
    "HTTPClient",
    "Exchange",
    "AsterDexClient",
    "round_size",
    "round_price"
]