#!/usr/bin/env python3
"""
Trade Intent Demo

This example demonstrates submitting trade intents for HyperLiquid trading.

Prerequisites:
- You must have a registered HyperETH API key
- You must have an approved agent wallet (that is managed by HyperETH)
"""

import os
import asyncio
import logging
import time
from hypereth_sdk import HyperETHClient, Exchange

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enable debug logging for all SDK components
# logging.getLogger('hypereth_sdk').setLevel(logging.DEBUG)


async def place_order_via_trade_intent(client: HyperETHClient, agent_wallet: str):
    """Demonstrate placing an order via trade intent (REST API)

    Args:
        client: HyperETH client instance
        agent_wallet: Agent wallet address
    """

    try:
        # Generate nonce (timestamp in milliseconds)
        nonce = int(time.time() * 1000)

        # 1. Place a limit order
        logger.info("Placing a limit order via trade intent...")

        # HyperLiquid action for placing an order
        order_action = {
            "action": {
                "type": "order",
                "grouping": "na",
                "orders": [
                    {
                        "a": 173,  # Asset index for DOGE
                        "b": True,  # Buy order
                        "p": "0.210",  # Price
                        "s": "50",  # Size
                        "r": False,  # Reduce-only
                        "t": {"limit": {"tif": "Gtc"}}  # Good-till-cancelled
                    }
                ]
            }
        }

        # Submit trade intent
        order_result = await client.submit_trade_intent(
            exchange=Exchange.HYPERLIQUID,
            action=order_action,
            agent_wallet=agent_wallet,
            nonce=nonce
        )

        if order_result.get("hl_response", {}).get("status") == "ok":
            logger.info("✓ Order placed successfully!")
            logger.info(f"  Intent Hash: {order_result.get('intent_hash')}")
            logger.info(f"  Aggregate Order ID: {order_result.get('agg_order_id')}")

            # Extract order ID if available
            order_data = order_result.get("hl_response", {}).get("response", {}).get("data", {})
            statuses = order_data.get("statuses", [])
            if statuses and isinstance(statuses[0], dict):
                order_id = statuses[0].get("resting", {}).get("oid")
                if order_id:
                    logger.info(f"  Order ID: {order_id}")
        else:
            logger.error(f"Failed to place order: {order_result}")
            return

        # Wait a moment
        await asyncio.sleep(2)

        # 2. Cancel the order (if we have an order ID)
        if 'order_id' in locals() and order_id:
            logger.info(f"\nCancelling order {order_id}...")

            cancel_nonce = int(time.time() * 1000)
            cancel_action = {
                "action": {
                    "type": "cancel",
                    "cancels": [
                        {
                            "a": 173,  # Asset index
                            "o": order_id  # Order ID to cancel
                        }
                    ]
                }
            }

            cancel_result = await client.submit_trade_intent(
                exchange=Exchange.HYPERLIQUID,
                action=cancel_action,
                agent_wallet=agent_wallet,
                nonce=cancel_nonce
            )

            if cancel_result.get("hl_response", {}).get("status") == "ok":
                logger.info(f"  Intent Hash: {cancel_result.get('intent_hash')}")
                statuses = cancel_result.get("hl_response", {}).get("response", {}).get("data", {}).get("statuses", [])

                # Check for errors in statuses array
                if statuses and isinstance(statuses[0], dict) and "error" in statuses[0]:
                    logger.error(f"✗ Order cancel failed: {statuses[0]['error']}")
                elif statuses and statuses[0] == "success":
                    logger.info("✓ Order cancelled successfully!")
                    logger.info("  Cancel Status: Success")
                else:
                    logger.info("✓ Order cancelled successfully!")
            else:
                logger.error(f"Failed to cancel order: {cancel_result}")

    except Exception as e:
        logger.error(f"Error in trade intent demo: {e}")


async def trade_intent_via_websocket(client: HyperETHClient, agent_wallet: str):
    """Demonstrate trade intent via WebSocket

    Args:
        client: HyperETH client instance
        agent_wallet: Agent wallet address
    """

    try:
        logger.info("Submitting trade intent via WebSocket...")

        nonce = int(time.time() * 1000)
        order_action = {
            "action": {
                "type": "order",
                "grouping": "na",
                "orders": [
                    {
                        "a": 173,
                        "b": True,
                        "p": "0.210",
                        "s": "50",
                        "r": False,
                        "t": {"limit": {"tif": "Gtc"}}
                    }
                ]
            }
        }

        # Submit via WebSocket
        ws_result = await client.submit_trade_intent_ws(
            exchange=Exchange.HYPERLIQUID,
            action=order_action,
            agent_wallet=agent_wallet,
            nonce=nonce
        )

        if ws_result.get("hl_response", {}).get("status") == "ok":
            logger.info("✓ WebSocket order placed successfully!")
            logger.info(f"  Intent Hash: {ws_result.get('intent_hash')}")
            logger.info(f"  Aggregate Order ID: {ws_result.get('agg_order_id')}")

            # Extract order ID if available
            order_data = ws_result.get("hl_response", {}).get("response", {}).get("data", {})
            statuses = order_data.get("statuses", [])
            if statuses and isinstance(statuses[0], dict):
                order_id = statuses[0].get("resting", {}).get("oid")
                if order_id:
                    logger.info(f"  Order ID: {order_id}")
        else:
            logger.error(f"Failed to place WebSocket order: {ws_result}")
            return

        # Wait a moment
        await asyncio.sleep(5)

        # 2. Cancel the order (if we have an order ID)
        if 'order_id' in locals() and order_id:
            logger.info(f"\nCancelling order {order_id} via WebSocket...")

            cancel_nonce = int(time.time() * 1000)
            cancel_action = {
                "action": {
                    "type": "cancel",
                    "cancels": [
                        {
                            "a": 173,  # Asset index
                            "o": order_id  # Order ID to cancel
                        }
                    ]
                }
            }

            cancel_result = await client.submit_trade_intent_ws(
                exchange=Exchange.HYPERLIQUID,
                action=cancel_action,
                agent_wallet=agent_wallet,
                nonce=cancel_nonce
            )

            if cancel_result.get("hl_response", {}).get("status") == "ok":
                logger.info(f"  Intent Hash: {cancel_result.get('intent_hash')}")
                statuses = cancel_result.get("hl_response", {}).get("response", {}).get("data", {}).get("statuses", [])

                # Check for errors in statuses array
                if statuses and isinstance(statuses[0], dict) and "error" in statuses[0]:
                    logger.error(f"✗ Order cancel failed: {statuses[0]['error']}")
                elif statuses and statuses[0] == "success":
                    logger.info("✓ Order cancelled successfully via WebSocket!")
                    logger.info("  Cancel Status: Success")
                else:
                    logger.info("✓ Order cancelled successfully via WebSocket!")
            else:
                logger.error(f"Failed to cancel WebSocket order: {cancel_result}")

    except Exception as e:
        logger.error(f"Error in WebSocket trade intent: {e}")


async def main():
    """Run all demos"""
    logger.info("=" * 60)
    logger.info("TRADE INTENT DEMO")
    logger.info("=" * 60)

    # Get API key and agent wallet once at the start
    api_key = os.getenv("HYPERETH_API_KEY")
    if api_key:
        print(f"🔑 Using API key from environment: {api_key[:8]}...")
    else:
        api_key = input("\nEnter your HyperETH API key (required): ").strip()
        if api_key:
            print(f"   Using provided API key: {api_key[:8]}...")
        else:
            print("\n❌ API key is required to use HyperETH.")
            return

    agent_wallet = os.getenv("AGENT_WALLET_ADDRESS")
    if agent_wallet:
        print(f"🔑 Using agent wallet from environment: {agent_wallet[:10]}...")
    else:
        agent_wallet = input("\nEnter your Agent Wallet address (required): ").strip()
        if not agent_wallet:
            print("\n❌ Agent Wallet address is required to submit trade intents.")
            return

    # Initialize client once - reused for both REST and WebSocket
    client = HyperETHClient(
        base_url = "https://api.hypereth.io",
        ws_url= "wss://api.hypereth.io/ws",
        api_key=api_key,
        environment="testnet"
    )

    try:
        # Connect WebSocket for the WebSocket demo
        await client.connect()

        # REST API demo
        logger.info("\n1. REST API Trade Intent:")
        logger.info("-" * 40)
        await place_order_via_trade_intent(client, agent_wallet)

        # WebSocket demo
        logger.info("\n2. WebSocket Trade Intent:")
        logger.info("-" * 40)
        await trade_intent_via_websocket(client, agent_wallet)

        logger.info("\n" + "=" * 60)
        logger.info("Demo completed!")

    finally:
        # Clean up connections
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())