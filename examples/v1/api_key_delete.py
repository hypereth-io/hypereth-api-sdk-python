#!/usr/bin/env python3
"""
Delete API Key Example

This example shows how to delete an API key from your HyperETH account.

The deletion process:
1. Signs a EIP-191 message: "HyperETH: Delete API Key: {api_key}" with nonce
2. Posts the API key and signature to DELETE /v1/api_key
3. Server recovers your wallet address and deletes the specified API key
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
    print("🗑️  HyperETH API Key Deletion")
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
            environment="" # No need to set environment for api key deletion
        )

        print(f"   Wallet Address: {client.wallet_address}")

        # Get API key to delete from user input
        print(f"\n🔑 Enter the API key you want to delete:")
        print(f"   (You can find your API keys using list_api_key.py)")

        api_key_to_delete = input("API Key: ").strip()

        if not api_key_to_delete:
            print("❌ No API key provided. Deletion cancelled.")
            return

        # Final confirmation
        print(f"\n⚠️  About to delete API key: {api_key_to_delete}")
        print(f"   This action cannot be undone!")
        final_confirm = input(f"   Type 'Y' to confirm: ")

        if final_confirm != 'Y':
            print("Deletion cancelled.")
            return

        # Delete the API key
        print(f"\n🗑️  Deleting API key...")
        print(f"   This will sign a message: 'HyperETH: Delete API Key: {api_key_to_delete}'")

        result = await client.delete_api_key(api_key_to_delete)

        if result.success:
            print(f"\n✅ API key deleted successfully!")
            print(f"   Deleted: {api_key_to_delete}")
            print(f"   Message: {result.message}")
            print(f"\n📋 Use list_api_key.py to see your remaining API keys.")

        else:
            print(f"\n❌ Failed to delete API key: {result.message}")
            print(f"\nTroubleshooting:")
            print(f"- Verify the API key exists and belongs to your wallet")
            print(f"- Check network connectivity")
            print(f"- Ensure the nonce timing is correct (within 1 minute)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nCommon issues:")
        print(f"- Private key format (should be 64 hex characters)")
        print(f"- Network connectivity")
        print(f"- Invalid API key format")
        print(f"- Server-side errors")


if __name__ == "__main__":
    asyncio.run(main())