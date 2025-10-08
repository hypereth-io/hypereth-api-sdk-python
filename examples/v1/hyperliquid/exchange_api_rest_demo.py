#!/usr/bin/env python3
"""
HyperETH Exchange API REST Demo

This example demonstrates complete order lifecycle using REST API:
1. Setup trading wallets
2. Place limit orders via REST
3. Cancel orders via REST
"""

import asyncio
import logging
import os
from hypereth_sdk import HyperETHClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable debug logging for all SDK components
# logging.getLogger('hypereth_sdk').setLevel(logging.DEBUG)


def get_api_key() -> str:
    """Get API key from environment or user input."""
    # Try environment first
    api_key = os.getenv('HYPERETH_API_KEY')
    if api_key:
        print(f"🔑 Using API key from environment: {api_key[:8]}...")
        return api_key

    api_key = input("\nEnter your HyperETH API key (required): ").strip()
    if api_key:
        print(f"   Using provided API key: {api_key[:8]}...")
        return api_key
    else:
        return None


async def demo_rest_trading():
    """Demonstrate REST trading lifecycle."""

    print("=" * 70)
    print("🚀 HyperETH Exchange API REST Demo")
    print("=" * 70)

    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ API key is required for exchange operations")
        return

    # Get private key
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        private_key = input("\nEnter your private key (for signing): ").strip()

    if not private_key:
        print("❌ Private key required for trading")
        return

    # Get environment
    use_testnet = input("Use testnet? (Y/n): ").lower().strip()
    environment = "testnet" if use_testnet not in ['n', 'no'] else "mainnet"

    print(f"\n🌐 Environment: {environment.upper()}")
    if environment == "mainnet":
        confirm = input("⚠️  MAINNET - Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            return

    try:
        # Initialize client
        async with HyperETHClient(
            base_url = "https://api.hypereth.io",
            ws_url= "wss://api.hypereth.io/ws",
            api_key=api_key,
            environment=environment
        ) as client:

            print(f"\n✅ Connected to HyperETH API")

            # Setup trading
            print(f"\n🔧 Setting up trading wallets...")

            # Set user wallet (for approving agent)
            user_info = client.hl.set_user_wallet(private_key)
            print(f"   User wallet: {user_info['user_address']}")

            # Create agent wallet (for trading)
            agent_info = client.hl.create_agent_wallet()
            print(f"   Agent wallet: {agent_info['agent_address']}")

            # Approve agent
            print(f"\n🔐 Approving agent wallet...")
            await client.hl.approve_agent()
            print(f"   ✅ Agent approved for trading")

            # Get market data
            print(f"\n📊 Getting market data...")
            mids = await client.hl.get_all_mids()
            if not mids:
                print("❌ Failed to get market data")
                return

            # Choose asset
            asset = 'DOGE'
            if asset not in mids:
                print(f"❌ Invalid asset: {asset}")
                return

            current_price = float(mids[asset])
            print(f"\n🎯 Trading {asset} at ${current_price:.6f}")

            # Calculate order size (target ~$15 order)
            target_value = 15.0
            order_size = target_value / current_price

            if asset == "DOGE":
                order_size = round(order_size)
            elif asset == "ETH":
                order_size = max(0.01, round(order_size, 4))
            else:
                order_size = round(order_size, 6)

            # Place REST order
            print(f"\n📈 STEP 1: Placing BUY order via REST API")
            print(f"   Size: {order_size} {asset}")
            print(f"   Will place 10% below market price")

            buy_response = await client.hl.place_order_rest(
                price="0",  # ignored since use_market_offset=True
                size=str(order_size),
                is_buy=True,
                asset=asset,
                use_market_offset=True,
                market_offset_pct=0.10
            )

            order_id = None
            asset_index = client.hl.asset_indices.get(asset, -1)

            if buy_response.get("status") == "ok":
                # Extract order ID
                response_data = buy_response.get("response", {})
                if response_data.get("type") == "order":
                    statuses = response_data.get("data", {}).get("statuses", [])
                    if statuses:
                        resting = statuses[0].get("resting", {})
                        order_id = resting.get("oid")

                        if order_id:
                            print(f"   ✅ REST order placed! ID: {order_id}")
                        else:
                            print(f"   ⚠️  Order may have filled immediately")
                else:
                    print(f"   📄 Response: {response_data}")
            else:
                print(f"   ❌ Order failed: {buy_response}")
                return

            # Wait
            print(f"\n⏳ STEP 2: Waiting 10 seconds...")
            await asyncio.sleep(10)

            # Check order status
            if order_id:
                print(f"\n📋 STEP 3: Checking order status")
                try:
                    if client.hl.user_wallet:
                        open_orders = await client.hl.get_user_open_orders(client.hl.user_wallet.address)
                        if isinstance(open_orders, list):
                            print(f"   Found {len(open_orders)} open orders")
                        else:
                            print(f"   Order status: {open_orders}")
                except Exception as e:
                    print(f"   Could not check order status: {e}")

            # Cancel order via REST
            if order_id:
                print(f"\n❌ STEP 4: Cancelling order {order_id} via REST API")
                cancel_response = await client.hl.cancel_order_rest(order_id, asset_index)

                if cancel_response.get("status") == "ok":
                    print(f"   ✅ Order cancelled via REST")
                else:
                    print(f"   ⚠️  Cancel may have failed: {cancel_response}")
            else:
                print(f"\n⏭️  No order to cancel")

            print(f"\n🎉 REST Demo completed!")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")


async def main():
    """Main function."""
    try:
        await demo_rest_trading()
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted")
    except Exception as e:
        print(f"\n💥 Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())