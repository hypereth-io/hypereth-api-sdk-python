#!/usr/bin/env python3
"""
Approve Builder Fee Example

This example shows how to approve the HyperETH builder fee using the HyperLiquid SDK.
"""

import os
import asyncio
from hypereth_sdk import HyperETHClient

# Use the hyperliquid-python-sdk for the actual builder fee approval
try:
    from hyperliquid.exchange import Exchange
    from hyperliquid.utils.constants import TESTNET_API_URL, MAINNET_API_URL
    from eth_account import Account
    HYPERLIQUID_SDK_AVAILABLE = True
except ImportError:
    HYPERLIQUID_SDK_AVAILABLE = False
    print("❌ HyperLiquid Python SDK not found!")
    print("   Install with: pip install hyperliquid-python-sdk")
    print("   This is required for approving builder fees.")
    exit(0)


async def main():
    print("🚀 HyperETH Builder Fee Approval")
    print("=" * 50)

    if not HYPERLIQUID_SDK_AVAILABLE:
        print("Please install the HyperLiquid Python SDK and try again.")
        return

    # Get private key from environment variable or prompt user
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        private_key = input("Enter your private key (or set PRIVATE_KEY env var): ")

    # Check if testnet should be used
    use_testnet_input = input("Use testnet? (Y/N): ").lower().strip()
    use_testnet = use_testnet_input in ['y', 'yes', 'true', '1']

    # Display environment
    print(f"\n🌐 Using {'TESTNET' if use_testnet else 'MAINNET'}")
    if not use_testnet:
        print("⚠️  WARNING: You are using MAINNET - real funds will be used!")
        confirm = input("Type 'yes' to continue with mainnet: ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return

    try:
        # Initialize HyperETH client to get builder fee info
        print("\n📋 Getting builder fee information...")

        # Create a minimal client to get builder info
        hypereth_client = HyperETHClient()
        builder_info = hypereth_client.get_builder_fee_info()

        # Display the simplified builder fee details
        print(f"   Builder Address: {builder_info['builder']}")
        print(f"   Fee Rate: {builder_info['fee']} basis points (0.{builder_info['fee']:02d}%)")

        # Create wallet from private key
        wallet = Account.from_key(private_key)
        print(f"   Your Address: {wallet.address}")

        # Initialize HyperLiquid Exchange with appropriate URL
        base_url = TESTNET_API_URL if use_testnet else MAINNET_API_URL
        exchange = Exchange(wallet, base_url=base_url)

        # Convert fee from basis points to percentage string format expected by HyperLiquid
        # 25bp = 0.25% = "0.25%"
        fee_percentage = f"{builder_info['fee'] / 100}%"

        print(f"\n🔐 Approving builder fee...")
        print(f"   This allows the HyperETH builder to collect up to {fee_percentage} fees")
        print(f"   Builder: {builder_info['builder']}")

        # Call the HyperLiquid SDK's approve_builder_fee method
        result = exchange.approve_builder_fee(builder_info['builder'], fee_percentage)

        print(f"\n✅ Success! Builder fee approved.")
        print(f"   Transaction result: {result}")

        print(f"\n🎉 You can now use the HyperETH API with this wallet!")
        print(f"   Next steps:")
        print(f"   1. Register an API key using register_api_key.py")
        print(f"   2. Use the API key for trading via HyperETH")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"- Make sure your private key is correct (64 hex characters)")
        print(f"- Check your internet connection")
        if use_testnet:
            print(f"- Get testnet ETH from a faucet if needed")


if __name__ == "__main__":
    asyncio.run(main())