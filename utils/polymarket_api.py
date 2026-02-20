#!/usr/bin/env python3
"""
Polymarket API Client
Official SDK wrapper for trading.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"').strip("'")
                os.environ.setdefault(key, value)


@dataclass
class PolymarketCredentials:
    """API credentials structure"""
    api_key: str
    secret: str
    passphrase: str


class PolymarketClient:
    """
    Polymarket trading client.
    
    Setup:
    1. Set PRIVATE_KEY env var (from wallet)
    2. Instantiate client
    3. Derive API credentials (auto from wallet)
    4. Trade
    """
    
    def __init__(self):
        self.client = None
        self.creds = None
        self.host = "https://clob.polymarket.com"
        self.gamma_host = "https://gamma-api.polymarket.com"
        self.chain_id = 137  # Polygon
        
    async def connect(self) -> bool:
        """
        Initialize connection to Polymarket.
        Requires PRIVATE_KEY in environment.
        """
        try:
            from py_clob_client.client import ClobClient
            
            private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
            if not private_key:
                raise ValueError("Set POLYMARKET_PRIVATE_KEY environment variable")
            
            # Step 1: Create temp client to derive credentials
            print("Deriving API credentials from wallet...")
            temp_client = ClobClient(
                self.host,
                key=private_key,
                chain_id=self.chain_id
            )
            
            # Step 2: Derive or create API key
            self.creds = temp_client.create_or_derive_api_creds()
            
            # Step 3: Create main trading client
            self.client = ClobClient(
                self.host,
                key=private_key,
                chain_id=self.chain_id,
                creds=self.creds,
                signature_type=0,  # EOA
                funder=os.getenv("POLYMARKET_ADDRESS", "")
            )
            
            print("Connected to Polymarket")
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    async def get_events(self, active: bool = True, limit: int = 50) -> List[Dict]:
        """
        Fetch active events (correct endpoint for live markets).
        
        Returns list of events with nested markets.
        """
        import requests
        
        try:
            response = requests.get(
                f"{self.gamma_host}/events",
                params={"active": str(active).lower(), "closed": "false", "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to fetch events: {e}")
            return []
    
    async def get_markets(self, active: bool = True, limit: int = 10) -> List[Dict]:
        """
        DEPRECATED: Use get_events() instead.
        Fetch active markets (may return stale data).
        """
        import requests
        
        try:
            response = requests.get(
                f"{self.gamma_host}/markets",
                params={"active": str(active).lower(), "closed": "false", "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to fetch markets: {e}")
            return []
    
    async def get_market(self, market_id: str) -> Optional[Dict]:
        """Get specific market by ID or slug"""
        import requests
        
        try:
            # Try by slug first
            response = requests.get(
                f"{self.gamma_host}/markets/{market_id}",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            
            # Fallback: search in active markets
            markets = await self.get_markets(active=True, limit=100)
            for m in markets:
                if m.get("market_slug") == market_id or m.get("id") == market_id:
                    return m
            return None
        except Exception as e:
            print(f"Failed to get market: {e}")
            return None
    
    async def get_order_book(self, token_id: str) -> Dict:
        """
        Get order book for a token (yes/no).
        
        Returns bids and asks.
        """
        if not self.client:
            raise RuntimeError("Not connected")
        
        try:
            return self.client.get_order_book(token_id)
        except Exception as e:
            print(f"Failed to get order book: {e}")
            return {}
    
    async def get_balance(self) -> Dict:
        """Get USDC balance"""
        if not self.client:
            raise RuntimeError("Not connected")
        
        try:
            return self.client.get_balance()
        except Exception as e:
            print(f"Failed to get balance: {e}")
            return {"balance": 0}
    
    async def place_order(
        self,
        token_id: str,
        side: str,  # "BUY" or "SELL"
        size: float,  # USDC amount
        price: Optional[float] = None  # Optional limit price
    ) -> Optional[Dict]:
        """
        Place an order.
        
        Args:
            token_id: Yes/No token ID from market
            side: BUY or SELL
            size: Amount in USDC
            price: Limit price (optional, market order if None)
        """
        if not self.client:
            raise RuntimeError("Not connected")
        
        try:
            from py_clob_client.order_builder.constants import BUY, SELL
            
            side_enum = BUY if side.upper() == "BUY" else SELL
            
            # If no price specified, use market price
            if price is None:
                ob = await self.get_order_book(token_id)
                if side_enum == BUY:
                    price = float(ob.get("asks", [[0, 1]])[0][0]) if ob.get("asks") else 0.5
                else:
                    price = float(ob.get("bids", [[0, 1]])[0][0]) if ob.get("bids") else 0.5
            
            order = self.client.create_order(
                token_id=token_id,
                side=side_enum,
                price=price,
                size=size
            )
            
            response = self.client.post_order(order)
            print(f"Order placed: {response}")
            return response
            
        except Exception as e:
            print(f"Failed to place order: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        if not self.client:
            raise RuntimeError("Not connected")
        
        try:
            self.client.cancel(order_id)
            return True
        except Exception as e:
            print(f"Failed to cancel order: {e}")
            return False
    
    async def get_open_orders(self) -> List[Dict]:
        """Get all open orders"""
        if not self.client:
            raise RuntimeError("Not connected")
        
        try:
            return self.client.get_orders()
        except Exception as e:
            print(f"Failed to get orders: {e}")
            return []
    
    def get_token_id(self, market: Dict, outcome: str) -> Optional[str]:
        """
        Get token ID for YES or NO outcome.
        
        Args:
            market: Market dict from get_markets
            outcome: "YES" or "NO"
        
        Returns:
            Token ID string
        """
        token_ids = market.get("clobTokenIds", [])
        if len(token_ids) < 2:
            return None
        
        # Index 0 = YES, Index 1 = NO
        return token_ids[0] if outcome.upper() == "YES" else token_ids[1]


# Test function
async def test_client():
    """Test the client (public data only - no private key needed)"""
    client = PolymarketClient()
    
    print("Testing public market fetch...")
    markets = await client.get_markets(active=True, limit=3)
    
    if markets:
        print(f"✅ Found {len(markets)} active markets")
        m = markets[0]
        print(f"\nSample market:")
        print(f"  Question: {m.get('question', 'N/A')}")
        print(f"  Slug: {m.get('slug', 'N/A')}")
        print(f"  Yes token: {m.get('clobTokenIds', ['?', '?'])[0][:20]}...")
        print(f"  No token:  {m.get('clobTokenIds', ['?', '?'])[1][:20]}...")
        return True
    else:
        print("❌ No markets found")
        return False


if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_client())
    exit(0 if result else 1)