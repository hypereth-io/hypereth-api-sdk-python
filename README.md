# HyperETH Python SDK

Python SDK for interacting with the HyperETH API.

## Prerequisites

- Python 3.8+

## Installation

```bash
git clone https://github.com/hypereth-io/hypereth-api-sdk-python
pip install -e .
```

## Getting Started (Trading on Hyperliquid with HyperETH)

The HyperETH SDK provides comprehensive examples that walk you through the complete trading setup and usage workflow. Follow these examples in order:

### 1. Approve Builder Fee (Required First Step)

Before you can start trading, you must approve the builder fee:

```bash
python examples/v1/hyperliquid/approve_builder_fee.py
```

**What it does:**
- Approves the HyperETH builder fee (25bp) for your wallet
- Required to perform any trading operations on HyperETH.
- One-time setup per wallet

**Requirements:** Main wallet private key

### 2. Register API Key

Once builder fee is approved, register your API key:

```bash
python examples/v1/api_key_register.py
```

**What it does:**
- Creates a new API key for your wallet
- Signs the registration using EIP-191 message signing
- Returns your new API key, which can be used to authenticate to other APIs on HyperETH.

**Requirements:** Main wallet private key (same as step 1)

### 3. Manage API Keys

List and manage your registered API keys:

```bash
# List all your API keys
python examples/v1/api_key_list.py

# Delete a specific API key
python examples/v1/api_key_delete.py
```

### 4. Test Market Data Access

Test your API key with market data queries:

```bash
python examples/v1/hyperliquid/info_api_demo.py
```

**What it does:**
- Retrieves market data via REST API
- Tests WebSocket subscriptions
- Show how to retrieve real-time price feeds and order book data

**Requirements:** API key (from step 2)

### 5. Exchange Trading

With a working API key, you can start performing basic trading actions:

#### REST API Trading
```bash
python examples/v1/hyperliquid/exchange_api_rest_demo.py
```

#### WebSocket Trading  
```bash
python examples/v1/hyperliquid/exchange_api_ws_demo.py
```

**What they do:**
- Set up trading wallets (agent wallet)
- Place and cancel orders

**Requirements:**
- API key (from step 2)
- Private key for signing transactions
- Sufficient balance for trading

## Managed Agent Wallet & Trade Intents

HyperETH provides managed agent wallets for trading with Trade Intents. Follow these steps to use Trade Intents on Hyperliquid:

### Step 1: Register Agent Wallet

Register a new managed agent wallet on HyperETH:

```bash
python examples/v1/hyperliquid/agent_wallet_demo.py
```

**What it does:**
- Registers a new managed agent wallet on HyperETH, approves the agent wallet on HyperCore via your main wallet.
- Lists all your agent wallets
- Shows agent wallet details (address, name, creation date)

**Requirements:**
- API key (from step 2)
- Main wallet private key

### Step 2: Trade Using Trade Intents

Once your agent wallet is approved, you can trade using Trade Intents:

```bash
python examples/v1/trade_intent_demo.py
```

**What it does:**
- Places orders via Trade Intent (both REST and WebSocket)
- Demonstrates order cancellation
- Uses your HyperETH-managed agent wallet

**Requirements:**
- API key (from step 2)
- Approved agent wallet address (from previous step)
