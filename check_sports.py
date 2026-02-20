#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""Check all markets - raw output"""
import asyncio, json
import requests

async def main():
    # Try different endpoints
    host = "https://gamma-api.polymarket.com"
    
    # Get markets with larger limit
    response = requests.get(
        f"{host}/markets",
        params={
            "active": "true", 
            "closed": "false", 
            "limit": 100,
            "sort": "volume"  # Sort by volume to get popular ones
        },
        timeout=15
    )
    
    markets = response.json()
    print(f"Fetched {len(markets)} markets\n")
    
    # Show all markets with their tags
    for i, m in enumerate(markets[:30]):
        question = m.get('question', '')
        end = m.get('endDate', 'N/A')[:10] if m.get('endDate') else 'N/A'
        vol = float(m.get('volume', 0)) / 1000
        tags = m.get('tags', [])
        slug = m.get('slug', '')
        
        # Check if sports-related
        is_sports = any(word in question.lower() for word in [
            'nba', 'nfl', 'super bowl', 'championship', 'playoff',
            'team', 'game', 'match', 'score', 'win', 'soccer', 
            'football', 'basketball', 'baseball', 'hockey', 'tennis'
        ])
        
        marker = "🏈 SPORTS" if is_sports else f"  {tags[0] if tags else 'other'}"
        
        print(f"{i+1:2}. {end} | Vol: ${vol:6.0f}K | {marker}")
        print(f"    {question[:70]}...")
        print()

if __name__ == "__main__":
    asyncio.run(main())
