#!/usr/bin/env python3
"""
HyperETH Agent Wallet Management Demo

This example demonstrates:
1. Registering a new agent wallet with HyperETH.
2. Listing all agent wallets
3. Deleting an agent wallet

Prerequisites:
- You must have a registered HyperETH API key
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

async def manage_agent_wallets():
    """Demonstrate agent wallet management"""

    # Get API key from environment
    api_key = os.getenv("HYPERETH_API_KEY")
    if api_key:
        print(f"🔑 Using API key from environment: {api_key[:8]}...")
    api_key = input("\nEnter your HyperETH API key (required): ").strip()
    if api_key:
        print(f"   Using provided API key: {api_key[:8]}...")
    else:
        print("\n❌ API key is required to use HyperETH.")
        return

    # Get private key from user
    private_key = input("\nEnter your private key (required): ").strip()
    if not private_key:
        print("\n❌ Private key is required to approve Agent Wallet.")
        return

    use_testnet_input = input("\nUse testnet? (Y/n): ").lower().strip()
    use_testnet = use_testnet_input not in ['n', 'no', 'false', '0']
    environment = "testnet" if use_testnet else "mainnet"

    # Initialize client with API key and private key
    client = HyperETHClient(
        base_url = "https://api.hypereth.io",
        ws_url= "wss://api.hypereth.io/ws",
        api_key=api_key,
        environment=environment,
        private_key=private_key
    )

    try:
        # 1. Register a new agent wallet
        logger.info("Registering new agent wallet...")
        register_result = await client.hl.register_agent_wallet("TestAgent")

        if register_result.get("address"):
            agent_address = register_result["address"]
            logger.info(f"✓ Agent wallet registered successfully!")
            logger.info(f"  Address: {agent_address}")
            logger.info(f"  Name: {register_result.get('name')}")
            logger.info(f"  Created: {register_result.get('created_at')}")

            # Approve agent wallet.
            logger.info("")
            logger.info(f"Approving agent wallet...")
            client.hl.set_agent_address(agent_address)
            approval_result = await client.hl.approve_agent()
            logger.info(f"✓ Agent address approved for trading on HyperLiquid!")
        else:
            logger.error(f"Failed to register agent wallet: {register_result}")
            return

        # 2. List all agent wallets
        logger.info("\nListing all agent wallets...")
        wallets = await client.hl.list_agent_wallets()

        if isinstance(wallets, list):
            logger.info(f"✓ Found {len(wallets)} agent wallet(s):")
            for wallet in wallets:
                logger.info(f"  - {wallet.get('name')} ({wallet.get('address')})")
                logger.info(f"    Active: {wallet.get('is_active')}")
                logger.info(f"    Created: {wallet.get('created_at')}")
        else:
            logger.error(f"Failed to list wallets: {wallets}")

        # 3. Delete the agent wallet (optional - for testing)
        # logger.info(f"\nDeleting agent wallet {agent_address}...")
        # delete_result = await client.hl.delete_agent_wallet(agent_address)

        # if delete_result.get("success") or delete_result.get("message"):
        #     logger.info(f"✓ Agent wallet deleted successfully")
        #     logger.info(f"  Message: {delete_result.get('message')}")
        #     if delete_result.get("note"):
        #         logger.info(f"  Note: {delete_result.get('note')}")
        # else:
        #     logger.error(f"Failed to delete wallet: {delete_result}")

        logger.info("💡 Notes:")
        logger.info("You can now use the agent wallet for trading via trade_intent!")

    except Exception as e:
        logger.error(f"Error managing agent wallets: {e}")


if __name__ == "__main__":
    asyncio.run(manage_agent_wallets())