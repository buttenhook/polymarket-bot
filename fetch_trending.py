#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""Fetch TRENDING markets from Polymarket"""
import asyncio
import requests
from datetime import datetime, timezone

async def main():
    host = "https://gamma-api.polymarket.com"
    
    print("Fetching trending/popular markets...")
    print("="*70)
    
    # Try different sort/filter options
    endpoints = [
        {"limit": 50, "active": "true", "sort": "volume", "order": "desc"},
        {"limit": 50, "active": "true", "sort": "liquidity", "order": "desc"},
        {"limit": 50, "active": "true", "sort": "competitive", "order": "desc"},
        {"limit": 50, "active": "true", "tag": "trending"},
    ]
    
    all_markets = {}
    
    for params in endpoints:
        try:
            r = requests.get(f"{host}/markets", params=params, timeout=15)
            markets = r.json()
            print(f"\nParams: {params}")
            print(f"Markets: {len(markets)}")
            
            for m in markets:
                mid = m.get("id")
                if mid not in all_markets:
                    all_markets[mid] = m
        except Exception as e:
            print(f"Error with {params}: {e}")
    
    # Sort by volume
    sorted_markets = sorted(all_markets.values(), 
                           key=lambda x: float(x.get("volume", 0) or 0), 
                           reverse=True)
    
    now = datetime.now(timezone.utc)
    
    print(f"\n\nTOP 20 MARKETS BY VOLUME:")
    print("="*70)
    print(f"{'Volume':<12} | {'End':<12} | Market")
    print("-"*70)
    
    for m in sorted_markets[:20]:
        vol = float(m.get("volume", 0) or 0) / 1000
        end = m.get("endDate", "N/A")[:10] if m.get("endDate") else "N/A"
        q = m.get("question", "N/A")[:45]
        
        # Check if ended
        status = ""
        if end != "N/A":
            try:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                days = (end_dt - now).days
                if days < 0:
                    status = "[ENDED]"
                else:
                    status = f"[{days}d]"
            except:
                pass
        
        print(f"${vol:>10.0f}K | {end:<12} | {q}... {status}")
    
    # Show trending/new
    print(f"\n\nRECENTLY ACTIVE (New or Breaking):")
    print("="*70)
    
    # Filter for markets with recent activity
    recent = [m for m in sorted_markets if m.get("active") and 
              float(m.get("volume", 0) or 0) > 1000000][:10]
    
    for m in recent:
        vol = float(m.get("volume", 0) or 0) / 1000
        end = m.get("endDate", "N/A")[:10] if m.get("endDate") else "N/A"
        q = m.get("question", "N/A")[:50]
        prices = m.get("prices", {})
        yes = prices.get("yes", 0)
        
        print(f"${vol:>8.0f}K | YES: {yes*100:.0f}% | {q}...")

if __name__ == "__main__":
    asyncio.run(main())
