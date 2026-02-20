#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3"""Check deportation market end dates"""
import asyncio
from utils.polymarket_api import PolymarketClient

async def check():
    c = PolymarketClient()
    markets = await c.get_markets(active=True, limit=50)
    
    for m in markets:
        q = m.get("question", "")
        if "deport" in q.lower():
            print(f"{q}")
            print(f"  End: {m.get('endDate', 'N/A')}")
            vol = float(m.get('volume', 0) or 0) / 1000
            print(f"  Volume: ${vol:.0f}K")
            print()

asyncio.run(check())
