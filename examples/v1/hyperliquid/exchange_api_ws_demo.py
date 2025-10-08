#!/usr/bin/env python3
"""
HyperETH Exchange API WebSocket Demo

This example demonstrates complete order lifecycle using WebSocket API:
1. Setup trading wallets
2. Place orders via WebSocket
3. Cancel orders via WebSocket
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
    """Get API key from environment or input."""
    # Try environment
    api_key = os.getenv('HYPERETH_API_KEY')
    if api_key:
        print(f"🔑 Using API key from environment: {api_key[:8]}...")
        return api_key

    api_key = input("\nEnter your HyperETH API key (required): ").strip()
    if api_key:
        print(f"   Using API key: {api_key[:8]}...")
        return api_key
    else:
        return None


async def demo_websocket_trading():
    """Demonstrate WebSocket trading with real-time updates."""

    print("=" * 70)
    print("🔌 HyperETH Exchange API WebSocket Demo")
    print("=" * 70)

    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ API key is required for WebSocket trading")
        return

    # Get private key
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        private_key = input("\nEnter your private key: ").strip()

    if not private_key:
        print("❌ Private key required")
        return

    # Get environment
    use_testnet = input("Use testnet? (Y/n): ").lower().strip()
    environment = "testnet" if use_testnet not in ['n', 'no'] else "mainnet"

    print(f"\n🌐 Environment: {environment.upper()}")
    if environment == "mainnet":
        confirm = input("⚠️  MAINNET WARNING - Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            return

    try:
        # Initialize WebSocket client
        async with HyperETHClient(
            base_url="https://api.hypereth.io",
            ws_url = "wss://api.hypereth.io/ws",
            api_key=api_key,
            environment=environment
        ) as client:

            print(f"\n✅ WebSocket connected with authentication")

            # Setup trading wallets
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
            print(f"   ✅ Agent approved for WebSocket trading")

            # Get market data via WebSocket
            print(f"\n💰 Getting market data via WebSocket...")
            market_data = await client.hl.send_ws_info_request({"type": "allMids"})

            if not market_data or "data" not in market_data:
                print("❌ Failed to get market data")
                return

            mids = market_data["data"]

            # Choose asset DOGE
            asset = 'DOGE'
            if asset not in mids:
                print(f"❌ Invalid asset: {asset}")
                return

            current_price = float(mids[asset])
            print(f"\n🎯 Trading {asset} at ${current_price:.6f}")

            # Calculate order size
            target_value = 15.0
            order_size = target_value / current_price

            if asset == "DOGE":
                order_size = round(order_size)
            elif asset == "ETH":
                order_size = max(0.01, round(order_size, 4))
            else:
                order_size = round(order_size, 6)

            print(f"\n🔄 Real-time Trading Demo:")
            print(f"   Placing buy order 10% below market")
            print(f"   Size: {order_size} {asset}")

            # Place order via WebSocket
            print(f"\n📈 STEP 1: Placing BUY order via WebSocket...")

            buy_response = await client.hl.place_order_ws(
                price="0",  # ignored
                size=str(order_size),
                is_buy=True,
                asset=asset,
                use_market_offset=True,
                market_offset_pct=0.10
            )

            order_id = None
            asset_index = client.hl.asset_indices.get(asset, -1)

            if buy_response.get("response", {}).get("payload", {}).get("status") == "ok":
                # Try to extract order ID from WebSocket response
                payload_response = buy_response["response"]["payload"].get("response", {})
                if payload_response.get("type") == "order":
                    statuses = payload_response.get("data", {}).get("statuses", [])
                    if statuses:
                        resting = statuses[0].get("resting", {})
                        order_id = resting.get("oid")

                        if order_id:
                            print(f"   ✅ WebSocket order placed! ID: {order_id}")
                        else:
                            print(f"   ⚠️  Order may have filled immediately")
                else:
                    print(f"   📄 Response: {payload_response}")
            else:
                print(f"   ❌ Order failed: {buy_response}")

            await asyncio.sleep(10)

            # Cancel order via WebSocket
            if order_id:
                print(f"\n❌ STEP 3: Cancelling order {order_id} via WebSocket...")
                cancel_response = await client.hl.cancel_order_ws(order_id, asset_index)

                if cancel_response.get("response", {}).get("payload", {}).get("status") == "ok":
                    print(f"   ✅ Order cancelled via WebSocket")
                else:
                    print(f"   ⚠️  Cancel response: {cancel_response}")
            else:
                print(f"\n⏭️  No order to cancel")

            print(f"\n🎉 WebSocket demo completed!")

    except Exception as e:
        logger.error(f"WebSocket demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")


async def main():
    """Main function."""
    try:
        await demo_websocket_trading()
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted")
    except Exception as e:
        print(f"\n💥 Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())