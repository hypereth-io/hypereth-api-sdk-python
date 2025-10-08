#!/usr/bin/env python3
"""
Register API Key Example

This example shows how to register a new API key with HyperETH.

The registration process:
1. Signs a EIP-191 message: "HyperETH: API Key Registration" with nonce
2. Posts the signature to POST /v1/api_key/register
3. Server recovers your wallet address and creates a new API key
"""

import os
import asyncio
from hypereth_sdk import HyperETHClient
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable debug logging for all SDK components
# logging.getLogger('hypereth_sdk').setLevel(logging.DEBUG)


async def main():
    print("🔑 HyperETH API Key Registration")
    print("=" * 50)

    # Get private key from environment variable or prompt user
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        private_key = input("Enter your private key (or set PRIVATE_KEY env var): ")

    try:
        # Initialize HyperETH client
        print("\n🔧 Initializing HyperETH client...")

        client = HyperETHClient(
            base_url="https://api.hypereth.io",
            private_key=private_key,
            environment="" # No need to set environment for api key registration
        )

        print(f"   Wallet Address: {client.wallet_address}")

        # Register new API key
        print(f"\n🔐 Registering new API key...")
        print(f"   This will sign a message: 'HyperETH: API Key Registration'")

        result = await client.register_api_key()

        if result.success:
            print(f"\n✅ Success! API key registered.")
            if result.api_key:
                print(f"   API Key: {result.api_key.key}")
                print(f"   Created: {result.api_key.created_at}")
                print(f"   Status: {'Active' if result.api_key.is_active else 'Inactive'}")
            print(f"   Message: {result.message}")

            print(f"\n🎉 You can now use this API key!")
            print(f"   Usage:")
            print(f"   - Include header: x-api-key: {result.api_key.key if result.api_key else '[your-key]'}")
            print(f"   - Use with HyperETH REST API and WebSocket connections")
            print(f"   - Manage keys with list_api_key.py and delete_api_key.py")
            print(f"   - Remember to approve builder fee if trading on HyperETH with Hyperliquid endpoints!")

        else:
            print(f"\n❌ Registration failed: {result.message}")
            print(f"\nTroubleshooting:")
            print(f"- Verify your private key is correct")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nCommon issues:")
        print(f"- Private key format (should be 64 hex characters)")
        print(f"- Network connectivity")


if __name__ == "__main__":
    asyncio.run(main())