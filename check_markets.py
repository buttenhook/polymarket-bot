#!/home/clawd/.openclaw/venv/trading-bot/bin/python3
"""Check available markets - filter by category"""
import asyncio, sys
from datetime import datetime
from utils.polymarket_api import PolymarketClient

def detect_category(question):
    q = question.lower()
    if any(w in q for w in ["bitcoin", "btc", "crypto", "ethereum"]):
        return "crypto"
    elif any(w in q for w in ["trump", "biden", "election", "senate", "congress", "elon", "doge", "federal", "deport"]):
        return "politics"
    elif any(w in q for w in ["super bowl", "nba", "nfl", "championship", "team", "game", "score", "win", "soccer", "football", "basketball"]):
        return "sports"
    elif any(w in q for w in ["gta", "game", "cost", "$100"]):
        return "gaming"
    else:
        return "other"

async def main():
    c = PolymarketClient()
    markets = await c.get_markets(active=True, limit=50)
    
    print(f'Found {len(markets)} markets\n')
    
    # Filter by category if arg provided
    category_filter = sys.argv[1] if len(sys.argv) > 1 else None
    
    print(f'END DATE     | CAT      | YES    | VOLUME   | MARKET')
    print('='*80)
    
    sports_count = 0
    
    for m in markets:
        question = m.get('question', '')
        end_date = m.get('endDate', '')[:10] if m.get('endDate') else 'N/A'
        
        # Try to get price
        try:
            yes_price = float(m.get('prices', {}).get('yes', 0)) * 100
        except:
            yes_price = 0
            
        try:
            volume = float(m.get('volume', 0)) / 1000
        except:
            volume = 0
            
        category = detect_category(question)
        
        # Show sports or all
        if category_filter:
            if category != category_filter:
                continue
        
        if category == "sports":
            sports_count += 1
            
        print(f'{end_date:12} | {category:8} | {yes_price:5.0f}% | {volume:6.0f}K | {question[:40]}...')

    print(f'\n{sports_count} sports markets found')

if __name__ == "__main__":
    asyncio.run(main())
