#!/usr/bin/env python3
"""
AsterDex Market API Demo

This example demonstrates using the HyperETH client to access AsterDex:
- Market data for perpetual futures (order books, trades, klines)
  - (Spot market is similar, replace `perp` with `spot` in general)
- WebSocket subscriptions for real-time updates
"""

import os
import asyncio
import logging
from hypereth_sdk import HyperETHClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enable debug logging for all SDK components
# logging.getLogger('hypereth_sdk').setLevel(logging.DEBUG)

async def demo_perp_markets(client: HyperETHClient):
    """Demonstrate perpetual futures market data access"""

    try:
        logger.info("Fetching AsterDex Perpetual Markets...")
        logger.info("-" * 40)

        # Get exchange info through client.aster using generic method
        markets = await client.aster.fapi_get("v1/exchangeInfo")

        if markets and "symbols" in markets:
            logger.info(f"✓ Found {len(markets['symbols'])} perpetual markets")

            # Show first few markets
            for symbol in markets['symbols'][:5]:
                logger.info(f"  - {symbol.get('symbol')}: {symbol.get('baseAsset')}/{symbol.get('quoteAsset')}")

        # Get order book for a specific symbol (example: BTCUSDT)
        symbol = "BTCUSDT"
        logger.info(f"\nFetching order book for {symbol}...")
        orderbook = await client.aster.fapi_get("v1/depth", params={"symbol": symbol, "limit": 5})

        if orderbook:
            logger.info(f"✓ Order book for {symbol}:")
            if "bids" in orderbook and orderbook["bids"]:
                logger.info(f"  Top Bid: {orderbook['bids'][0][0]} @ {orderbook['bids'][0][1]}")
            if "asks" in orderbook and orderbook["asks"]:
                logger.info(f"  Top Ask: {orderbook['asks'][0][0]} @ {orderbook['asks'][0][1]}")

        # Get recent trades
        logger.info(f"\nFetching recent trades for {symbol}...")
        trades = await client.aster.fapi_get("v1/trades", params={"symbol": symbol, "limit": 5})

        if trades and isinstance(trades, list) and len(trades) > 0:
            logger.info(f"✓ Recent trades for {symbol}:")
            for trade in trades[:3]:
                side = "BUY" if trade.get("isBuyerMaker") else "SELL"
                logger.info(f"  - {side}: {trade.get('qty')} @ {trade.get('price')}")

        # Get klines
        logger.info(f"\nFetching 1h klines for {symbol}...")
        klines = await client.aster.fapi_get("v1/klines", params={"symbol": symbol, "interval": "1h", "limit": 5})

        if klines and isinstance(klines, list) and len(klines) > 0:
            logger.info(f"✓ Recent klines for {symbol}:")
            for kline in klines[:3]:
                logger.info(f"  - Open: {kline[1]}, High: {kline[2]}, Low: {kline[3]}, Close: {kline[4]}")

    except Exception as e:
        logger.error(f"Error in perpetual markets demo: {e}")

async def demo_websocket_subscriptions(client: HyperETHClient):
    """Demonstrate WebSocket subscriptions"""

    try:
        logger.info("\nWebSocket Subscription Demo...")
        logger.info("-" * 40)

        symbol = "BTCUSDT"

        # Subscribe to perpetual streams using AsterDex format
        # Format: symbol@stream (e.g., "btcusdt@depth", "btcusdt@aggTrade")
        logger.info(f"Subscribing to perpetual streams for {symbol}...")
        perp_streams = [
            f"{symbol.lower()}@depth",     # Order book updates
            f"{symbol.lower()}@aggTrade"   # Aggregated trade updates
        ]
        await client.aster.subscribe_perp_streams(perp_streams)
        logger.info("✓ Subscribed to perpetual order book and trade updates")

        logger.info("\nListening for updates for 5 seconds...")
        await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"Error in WebSocket demo: {e}")


async def main():
    """Run all AsterDex demos"""
    logger.info("=" * 60)
    logger.info("ASTERDEX API DEMO")
    logger.info("=" * 60)

    # Get API key
    api_key = os.getenv("HYPERETH_API_KEY")

    if api_key:
        logger.info(f"🔑 Using API key from environment: {api_key[:8]}...")
    else:
        api_key = input("\nEnter your HyperETH API key: ").strip()
        if api_key:
            logger.info(f"   Using provided API key: {api_key[:8]}...")
        else:
            print("❌ API key is required")
            return

    # Initialize HyperETH client once for all demos
    client = HyperETHClient(
        base_url="https://api.hypereth.io",
        ws_url="wss://api.hypereth.io/ws",
        api_key=api_key
    )

    try:
        # Perpetual markets demo
        await demo_perp_markets(client)

        # WebSocket demo
        await demo_websocket_subscriptions(client)

        logger.info("\n" + "=" * 60)
        logger.info("AsterDex demo completed!")

    finally:
        # Clean up WebSocket connections
        await client.aster.disconnect_ws()
        logger.info("WebSocket connections closed")


if __name__ == "__main__":
    asyncio.run(main())