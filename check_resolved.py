#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""Check if markets are resolved"""
import asyncio
from utils.polymarket_api import PolymarketClient

async def check():
    c = PolymarketClient()
    
    # Get both active and closed markets
    all_markets = await c.get_markets(active=True, limit=100)
    
    print("Checking deportation markets...")
    print(f"Total active markets: {len(all_markets)}")
    print()
    
    deport_markets = []
    for m in all_markets:
        q = m.get("question", "")
        if "deport" in q.lower():
            deport_markets.append(m)
            
            print(f"Market: {q}")
            print(f"  Status: {m.get('status', 'N/A')}")
            print(f"  Active: {m.get('active', 'N/A')}")
            print(f"  End Date: {m.get('endDate', 'N/A')}")
            print(f"  Resolved: {m.get('isResolved', 'N/A')}")
            print(f"  Outcome: {m.get('outcome', 'N/A')}")
            
            # Check current prices
            prices = m.get("prices", {})
            yes = prices.get("yes", "N/A")
            no = prices.get("no", "N/A")
            print(f"  Current YES: {yes}")
            print(f"  Current NO: {no}")
            print()
    
    if not deport_markets:
        print("No deportation markets found in active markets!")
        print("They may be resolved/closed.")

asyncio.run(check())
