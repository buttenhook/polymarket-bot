#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""Fetch LIVE events using correct API endpoint"""
import asyncio
import requests
from datetime import datetime, timezone

async def main():
    host = "https://gamma-api.polymarket.com"
    
    print("="*70)
    print("LIVE EVENTS (using /events with active=true&closed=false)")
    print("="*70)
    
    # Get live events
    r = requests.get(
        f"{host}/events?active=true&closed=false&limit=50",
        timeout=15
    )
    events = r.json()
    
    print(f"\nFound {len(events)} live events")
    print()
    
    now = datetime.now(timezone.utc)
    
    for i, e in enumerate(events[:15]):
        title = e.get("title", "N/A")
        end_date = e.get("endDate", "N/A")
        slug = e.get("slug", "N/A")
        volume = float(e.get("volume", 0) or 0) / 1000
        liquidity = float(e.get("liquidity", 0) or 0) / 1000
        
        # Calculate days until
        days_until = "N/A"
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                days_until = (end_dt - now).days
            except:
                pass
        
        print(f"{i+1}. {title}")
        print(f"   Slug: {slug}")
        print(f"   End: {end_date[:10] if end_date else 'N/A'} ({days_until} days)")
        print(f"   Volume: ${volume:.0f}K | Liquidity: ${liquidity:.0f}K")
        
        # Show markets within event
        markets = e.get("markets", [])
        for m in markets[:2]:
            question = m.get("question", "")
            prices = m.get("prices", {})
            yes_price = prices.get("yes", 0) * 100
            print(f"   -> {question[:50]}... (YES: {yes_price:.0f}%)")
        if len(markets) > 2:
            print(f"   ... and {len(markets)-2} more markets")
        print()

if __name__ == "__main__":
    asyncio.run(main())
