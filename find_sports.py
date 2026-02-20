#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""Find sports markets via different endpoints"""
import asyncio, json
import requests

async def main():
    host = "https://gamma-api.polymarket.com"
    
    # Try events endpoint
    print("=== EVENTS ===")
    try:
        events = requests.get(f"{host}/events?active=true&limit=50", timeout=15).json()
        print(f"Found {len(events)} events\n")
        
        sports_events = []
        for e in events[:20]:
            title = e.get('title', '')
            if any(word in title.lower() for word in ['nba', 'nfl', 'sports', 'game', 'match', 'championship', 'super bowl', 'soccer', 'football']):
                sports_events.append(e)
                print(f"🏈 {title}")
                print(f"   End: {e.get('endDate', 'N/A')}")
                print(f"   Volume: ${e.get('volume', 0)/1000:.0f}K")
                print()
        
        if not sports_events:
            print("No sports events found in first 20")
            # Show all events with tags
            for e in events[:10]:
                print(f"Event: {e.get('title')}")
                print(f"  Tags: {e.get('tags', [])}")
                print()
    except Exception as e:
        print(f"Events error: {e}")
    
    # Try markets with category filter
    print("\n=== MARKETS WITH TAGS ===")
    markets = requests.get(f"{host}/markets?active=true&limit=100", timeout=15).json()
    
    # Count by tag
    tag_counts = {}
    for m in markets:
        for tag in m.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    print("Tags found:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {tag}: {count}")
    
    # Look for sports in description
    print("\n=== SEARCHING FOR SPORTS KEYWORDS ===")
    sports_keywords = ['nba', 'nfl', 'playoff', 'championship', 'super bowl', 'world cup', 'soccer', 'football', 'basketball']
    
    found = 0
    for m in markets:
        text = f"{m.get('question', '')} {m.get('description', '')}".lower()
        if any(kw in text for kw in sports_keywords):
            found += 1
            print(f"🏈 {m.get('question')[:60]}...")
            print(f"   End: {m.get('endDate', 'N/A')}")
            print(f"   Tags: {m.get('tags', [])}")
            print()
            if found >= 10:
                break
    
    if found == 0:
        print("No sports markets found with keyword search")
        print("\nSample market questions:")
        for m in markets[:5]:
            print(f"  - {m.get('question')}")

if __name__ == "__main__":
    asyncio.run(main())
