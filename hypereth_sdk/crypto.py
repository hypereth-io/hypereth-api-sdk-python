"""
Cryptographic utilities for wallet interactions and message signing
"""

import hashlib
import secrets
from typing import Union
from eth_account import Account
from eth_account.messages import encode_defunct
from .exceptions import SigningError, ValidationError


class WalletSigner:
    """Handles wallet operations and message signing"""

    def __init__(self, private_key: str):
        """
        Initialize wallet signer with private key

        Args:
            private_key: Hex string private key (with or without 0x prefix)
        """
        if not private_key:
            raise ValidationError("Private key is required")

        # Ensure private key has 0x prefix
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key

        try:
            self.account = Account.from_key(private_key)
        except Exception as e:
            raise ValidationError(f"Invalid private key: {e}")

    @property
    def address(self) -> str:
        """Get wallet address"""
        return self.account.address

    def generate_nonce(self) -> int:
        """Generate a timestamp-based nonce in milliseconds"""
        import time
        return int(time.time() * 1000)

    def sign_message(self, message: str, nonce: int) -> tuple[str, str]:
        """
        Sign a message with nonce

        Args:
            message: The message to sign
            nonce: Nonce to include in the message

        Returns:
            Tuple of (signed_message, signature)
        """
        try:
            # Create the full message with nonce
            full_message = f"{message}\nNonce: {nonce}"

            # Encode message for signing
            encoded_message = encode_defunct(text=full_message)

            # Sign the message
            signed_message = self.account.sign_message(encoded_message)

            return full_message, signed_message.signature.hex()

        except Exception as e:
            raise SigningError(f"Failed to sign message: {e}")

    def sign_registration_message(self, nonce: int) -> tuple[str, str]:
        """Sign API key registration message"""
        return self.sign_message("HyperETH: API Key Registration", nonce)

    def sign_list_message(self, nonce: int) -> tuple[str, str]:
        """Sign API key list message"""
        return self.sign_message("HyperETH: List All API Keys", nonce)

    def sign_delete_message(self, api_key: str, nonce: int) -> tuple[str, str]:
        """Sign API key deletion message"""
        return self.sign_message(f"HyperETH: Delete API Key: {api_key}", nonce)
