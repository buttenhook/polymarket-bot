#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""Verify bot can pull CURRENT markets (future dates only)"""
import asyncio
from datetime import datetime, timezone
from utils.polymarket_api import PolymarketClient

async def main():
    print("="*70)
    print("VERIFYING CURRENT MARKETS")
    print(f"Today: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("="*70)
    
    c = PolymarketClient()
    markets = await c.get_markets(active=True, limit=100)
    
    print(f"\nFetched {len(markets)} total markets")
    print("\n" + "="*70)
    print("LIVE MARKETS (end date in future):")
    print("="*70)
    print(f"{'End Date':<12} | {'Days':<5} | {'Volume':<8} | Market")
    print("-"*70)
    
    live_count = 0
    now = datetime.now(timezone.utc)
    
    for m in markets:
        end_date = m.get("endDate", "")
        if not end_date:
            continue
            
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
            days_until = (end_dt - now).days
            
            if days_until >= 0:
                live_count += 1
                vol = float(m.get("volume", 0) or 0) / 1000
                q = m.get("question", "")[:45]
                
                print(f"{end_date[:10]} | {days_until:>4}d | ${vol:>6.0f}K | {q}...")
                
        except Exception as e:
            continue
    
    print("-"*70)
    print(f"\nFound {live_count} markets with future end dates")
    print(f"Filtered out {len(markets) - live_count} markets (already ended)")
    
    if live_count == 0:
        print("\n⚠️  WARNING: No live markets found!")
        print("   The API may be returning cached/stale data.")

if __name__ == "__main__":
    asyncio.run(main())
