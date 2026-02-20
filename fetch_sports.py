#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
import requests, json, asyncio
from datetime import datetime

host = "https://gamma-api.polymarket.com"

def fetch_by_category(category, limit=50):
    """Fetch markets by category field"""
    try:
        r = requests.get(
            f"{host}/markets",
            params={"category": category, "active": "true", "limit": limit},
            timeout=15
        )
        return r.json()
    except Exception as e:
        print(f"Error: {e}")
        return []

async def main():
    # Try different sports categories
    categories = ["Sports", "sports", "NBA", "nba", "NFL", "nfl", "NHL", "nhl", 
                  "Soccer", "soccer", "Tennis", "tennis", "UFC", "ufc",
                  "UCL", "EPL", "MLB", "NCAAB", "ATP", "LoL", "Valorant"]
    
    print("Searching for sports markets by category\n")
    print(f"{'Category':<15} {'Markets':<10} {'End Soonest'}")
    print("-" * 60)
    
    for cat in categories:
        markets = fetch_by_category(cat, limit=20)
        if markets and len(markets) > 0:
            # Get nearest end date
            end_dates = []
            for m in markets:
                ed = m.get('endDate')
                if ed:
                    try:
                        end_dates.append(datetime.fromisoformat(ed.replace('Z', '+00:00')))
                    except:
                        pass
            
            nearest = min(end_dates).strftime('%Y-%m-%d') if end_dates else 'N/A'
            print(f"{cat:<15} {len(markets):<10} {nearest}")
            
            # Show sample
            for m in markets[:2]:
                print(f"  -> {m.get('question', 'N/A')[:50]}... | End: {m.get('endDate', '')[:10]}")
    
    # Also try fetching ALL and filtering
    print("\n" + "="*60)
    print("Scanning ALL markets for sports keywords")
    print("="*60)
    
    all_markets = requests.get(f"{host}/markets?active=true&limit=300").json()
    
    sports_keywords = ['nba', 'nfl', 'nhl', 'playoff', 'championship', 'bulls', 'lakers', 
                       'celtics', 'warriors', 'knicks', 'pacers', 'bucks', 'heat', 'magic',
                       'suns', 'thunder', 'nuggets', 'timberwolves',
                       'soccer', 'uefa', 'epl', 'la liga', 'bundesliga', 'champions',
                       'tennis', 'ufc', 'atp', 'wta', 'lol', 'valorant', 'dota', 'cs2']
    
    sports_markets = []
    for m in all_markets:
        q = m.get('question', '').lower()
        if any(kw in q for kw in sports_keywords):
            # Check if recently ending
            end = m.get('endDate', '')
            try:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                days_until = (end_dt - datetime.now(end_dt.tzinfo)).days
            except:
                days_until = 999
            
            sports_markets.append((m, days_until))
    
    # Sort by days until end
    sports_markets.sort(key=lambda x: x[1])
    
    print(f"\nFound {len(sports_markets)} sports markets")
    print("\nEnding SOONEST (next 7 days):")
    print("-"*70)
    
    for m, days in sports_markets[:10]:
        if days < 7:
            print(f"{days:2}d | {m.get('endDate', 'N/A')[:10]} | {m.get('question', 'N/A')[:55]}...")
            print(f"     Vol: ${float(m.get('volume', 0))/1000:.0f}K | Yes: {float(m.get('prices', {}).get('yes', 0))*100:.0f}%")

if __name__ == "__main__":
    asyncio.run(main())
