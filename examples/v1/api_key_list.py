#!/usr/bin/env python3
"""
List API Keys Example

This example shows how to list all API keys associated with your wallet.

The listing process:
1. Signs a EIP-191 message: "HyperETH: List All API Keys" with nonce
2. Posts the signature to POST /v1/api_key/list
3. Server recovers your wallet address and returns all associated API keys
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
    print("📋 HyperETH API Key Listing")
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
            environment="" # No need to set environment for api key listing
        )

        print(f"   Wallet Address: {client.wallet_address}")

        # List API keys
        print(f"\n🔍 Retrieving API keys...")
        print(f"   This will sign a message: 'HyperETH: List All API Keys'")

        result = await client.list_api_keys()

        if result.success:
            if result.api_keys and len(result.api_keys) > 0:
                print(f"\n✅ Found {len(result.api_keys)} API key(s):")
                print("-" * 80)

                for i, api_key in enumerate(result.api_keys, 1):
                    print(f"\n{i}. API Key: {api_key.key}")
                    if api_key.created_at:
                        print(f"   Created: {api_key.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    if api_key.last_used:
                        print(f"   Last Used: {api_key.last_used.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    else:
                        print(f"   Last Used: Never")
                    print(f"   Status: {'✅ Active' if api_key.is_active else '❌ Inactive'}")

                print("-" * 80)
                print(f"\n💡 Tips:")
                print(f"   - Use these keys in the 'x-api-key' header")
                print(f"   - Delete unused keys with delete_api_key.py")
                print(f"   - Keep your keys secure and don't share them")

            else:
                print(f"\n📭 No API keys found for this wallet.")
                print(f"   Create one with register_api_key.py")

            if result.message:
                print(f"\n📨 Server message: {result.message}")

        else:
            print(f"\n❌ Failed to list API keys: {result.message}")
            print(f"\nTroubleshooting:")
            print(f"- Verify your private key is correct")
            print(f"- Check network connectivity")
            print(f"- Ensure the nonce timing is correct (within 1 minute)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nCommon issues:")
        print(f"- Private key format (should be 64 hex characters)")
        print(f"- Network connectivity")


if __name__ == "__main__":
    asyncio.run(main())