#!/usr/bin/env python3
"""
HyperETH Info API Demo

This example demonstrates how to retrieve market data using the HyperETH SDK
with both HyperLiquid integration and API key authentication.

Features:
- REST API queries to /info endpoint
- WebSocket subscriptions for real-time data
- x-api-key header support
"""

import asyncio
import logging
import time
import os
from hypereth_sdk import HyperETHClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable debug logging for all SDK components
# logging.getLogger('hypereth_sdk').setLevel(logging.DEBUG)

async def demo_rest_queries(client: HyperETHClient):
    """Demonstrate various REST API queries."""

    print("\n=== REST API Queries ===")

    # Get all mid prices via REST
    print("\n1. Getting all mid prices via REST API...")
    mids = await client.hl.get_all_mids()
    if mids:
        # Show a few example prices
        examples = ["ETH", "BTC", "DOGE", "SOL", "ARB"]
        for coin in examples:
            if coin in mids:
                print(f"   {coin}: ${mids[coin]}")

    # Get L2 order book for ETH via REST
    print("\n2. Getting L2 order book for ETH via REST API...")
    book = await client.hl.get_l2_book("ETH")
    if book and "levels" in book:
        levels = book["levels"]
        if len(levels) >= 2:
            bids = levels[0][:3] if levels[0] else []
            asks = levels[1][:3] if levels[1] else []

            print("   Top 3 Bids:")
            for bid in bids:
                print(f"     Price: ${bid['px']}, Size: {bid['sz']}")

            print("   Top 3 Asks:")
            for ask in asks:
                print(f"     Price: ${ask['px']}, Size: {ask['sz']}")

    # Get metadata via REST
    print("\n3. Getting metadata via REST API...")
    meta = await client.hl.get_meta()
    if meta and "universe" in meta:
        print(f"   Total assets: {len(meta['universe'])}")
        # Show first few assets
        for i, asset in enumerate(meta['universe'][:5]):
            name = asset.get('name', 'Unknown')
            sz_decimals = asset.get('szDecimals', 0)
            print(f"   {i}: {name} (szDecimals: {sz_decimals})")

    # Test error handling with REST API
    print("\n4. Testing error handling with invalid coin (REST API)...")
    try:
        book = await client.hl.get_l2_book("INVALID_COIN")
        print(f"   Response: {book}")
    except Exception as e:
        print(f"   Error: {e}")


async def demo_websocket_queries(client: HyperETHClient):
    """Demonstrate WebSocket API queries and subscriptions."""

    print("\n=== WebSocket API Queries ===")

    # Get historical candles via WebSocket
    print("\n5. Getting recent DOGE candle data via WebSocket (last hour)...")
    try:
        end_time = int(time.time() * 1000)  # Current time in ms
        start_time = end_time - (60 * 60 * 1000)  # 1 hour ago

        candles = await client.hl.get_candle_snapshot("DOGE", "5m", start_time, end_time)
        if candles and "data" in candles:
            candle_data = candles["data"]
            print(f"   Retrieved {len(candle_data)} candles for the last hour")
            if candle_data:
                latest = candle_data[-1]
                print(f"   Latest 5m candle:")
                print(f"     Time: {latest.get('T', 'N/A')}")
                print(f"     Open: ${latest.get('o', 'N/A')}")
                print(f"     High: ${latest.get('h', 'N/A')}")
                print(f"     Low: ${latest.get('l', 'N/A')}")
                print(f"     Close: ${latest.get('c', 'N/A')}")
                print(f"     Volume: {latest.get('v', 'N/A')}")
    except Exception as e:
        print(f"   Error getting candles: {e}")

    # Get data via WebSocket POST method
    print("\n6. Getting exchange status via WebSocket POST...")
    try:
        payload = {"type": "exchangeStatus"}
        response = await client.hl.send_ws_info_request(payload)
        if response and "data" in response:
            status = response["data"]
            print(f"   Exchange status retrieved: {status}")
    except Exception as e:
        print(f"   Failed to get exchange status: {e}")

    print("\n7. Subscribing to real-time mid prices via WebSocket...")
    await client.hl.subscribe_to_channel("allMids")

    print("   Listening for 5 seconds...")
    await asyncio.sleep(5)

    print("   Unsubscribing from allMids...")
    await client.hl.unsubscribe_from_channel("allMids")
    await asyncio.sleep(5)


async def main():
    """Main demo function."""

    print("="*60)
    print("HyperETH Info API Demo")
    print("="*60)

    # Get API key from environment or input
    api_key = os.getenv('HYPERETH_API_KEY')
    if api_key:
        print(f"🔑 Using API key from environment: {api_key[:8]}...")
    else:
        api_key = input("\nEnter your HyperETH API key (required): ").strip()
        if api_key:
            print(f"   Using provided API key: {api_key[:8]}...")
        else:
            print("❌ API key is required")
            return

    # Check if testnet should be used
    use_testnet_input = input("\nUse testnet? (Y/n): ").lower().strip()
    use_testnet = use_testnet_input not in ['n', 'no', 'false', '0']
    environment = "testnet" if use_testnet else "mainnet"

    print(f"🌐 Environment: {environment.upper()}")
    print(f"📡 Base URL: https://api.hypereth.io/v1/hl")
    print(f"🔌 WebSocket URL: wss://api.hypereth.io/v1/hl/ws")
    print("\nThis demo shows data retrieval via both REST and WebSocket APIs")
    print()

    try:
        # Use the client with async context manager
        async with HyperETHClient(
            base_url="https://api.hypereth.io",
            environment=environment,
            api_key=api_key,
            ws_url="wss://api.hypereth.io/ws"
        ) as client:

            # Demo REST API queries
            await demo_rest_queries(client)

            # Demo WebSocket API queries and subscriptions
            await demo_websocket_queries(client)

            print("\n" + "="*60)
            print("Demo completed successfully!")
            print("="*60)

    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("- Check your internet connection")
        print("- Verify the API key is valid")
        print("- Ensure the HyperETH API is accessible")


if __name__ == "__main__":
    asyncio.run(main())