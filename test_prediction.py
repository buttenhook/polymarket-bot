#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""
Test Script: Web Search Prediction Demo
Shows how the bot would analyze a Polymarket market using real search.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List

# Sample markets to test
SAMPLE_MARKETS = [
    {
        "question": "Will Bitcoin hit $100000 by March 31 2026?",
        "category": "crypto",
        "current_odds": 0.35,
        "market_id": "sample-btc-100k"
    }
]

def build_search_query(question: str, category: str) -> str:
    """Convert market question to search query."""
    query = question.lower()
    for word in ["will", "by", "the", "in", "on", "if", "?"]:
        query = query.replace(word, " ")
    
    context = {
        "crypto": "price prediction analysis forecast latest 2026",
    }
    
    if category in context:
        query += f" {context[category]}"
    
    return query.strip()

def analyze_sentiment(text: str) -> float:
    """Simple sentiment analysis: -1.0 to +1.0"""
    text = text.lower()
    positive_words = ["bull", "bullish", "rally", "surge", "strong", "growth", " ATH", "confident"]
    negative_words = ["bear", "bearish", "crash", "dump", "fall", "weak", "correction"]
    
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    
    return (pos_count - neg_count) / total

def calculate_probability(results: List[Dict], current_odds: float) -> Dict:
    """Calculate prediction from search results."""
    if not results:
        return {
            "direction": "UNKNOWN",
            "prob_yes": current_odds,
            "confidence": 0.0,
            "reasoning": "No data",
            "sentiment": 0.0
        }
    
    total_sentiment = 0
    for result in results[:3]:
        text = f"{result.get('title', '')} {result.get('snippet', '')}"
        total_sentiment += analyze_sentiment(text)
    
    avg_sentiment = total_sentiment / 3
    prob_adjustment = avg_sentiment * 0.3
    predicted_prob = current_odds + prob_adjustment
    predicted_prob = max(0.05, min(0.95, predicted_prob))
    
    confidence = min(0.5 + (abs(avg_sentiment) * 0.3), 0.9)
    direction = "YES" if predicted_prob > current_odds else "NO"
    
    return {
        "direction": direction,
        "prob_yes": round(predicted_prob, 2),
        "market_odds": current_odds,
        "confidence": round(confidence, 2),
        "sentiment": round(avg_sentiment, 2),
        "reasoning": f"{'Bullish' if avg_sentiment > 0 else 'Bearish'} sentiment detected"
    }

def mock_web_search(query: str) -> List[Dict]:
    """Simulated web search."""
    return [
        {"title": "Analyst predicts BTC rally", "snippet": "Bullish momentum expected"},
        {"title": "Market shows strength", "snippet": "Technical indicators positive"}
    ]

async def test_market(market: Dict) -> Dict:
    """Test prediction on a single market."""
    print(f"\n{'='*60}")
    print(f"MARKET: {market['question']}")
    print(f"CURRENT ODDS: {market['current_odds']*100:.0f}%")
    print('='*60)
    
    query = build_search_query(market['question'], market['category'])
    print(f"\n1. Search Query: '{query}'")
    
    print("2. Searching...")
    results = mock_web_search(query)
    print(f"   Found {len(results)} sources")
    
    print("3. Analyzing sentiment...")
    prediction = calculate_probability(results, market['current_odds'])
    
    print(f"\n--- PREDICTION ---")
    print(f"  Direction: {prediction['direction']}")
    print(f"  Our Prediction: {prediction['prob_yes']*100:.0f}%")
    print(f"  Market Odds: {prediction['market_odds']*100:.0f}%")
    print(f"  Confidence: {prediction['confidence']*100:.0f}%")
    print(f"  Sentiment: {prediction['sentiment']:+.2f}")
    print(f"  Edge: {abs(prediction['prob_yes'] - prediction['market_odds'])*100:.0f}%")
    
    if prediction['confidence'] > 0.65:
        print(f"\n  TRADE: {prediction['direction']} (High confidence + edge)")
    else:
        print(f"\n  NO TRADE: Low confidence")
    
    return prediction

async def main():
    """Run test."""
    print("\n" + "="*60)
    print("POLYMARKET BOT - DEMO")
    print("="*60)
    print("Shows web search + sentiment analysis flow")
    
    for market in SAMPLE_MARKETS:
        await test_market(market)
    
    print("\n" + "="*60)
    print("Flow complete!")
    print("Real bot uses live web_search + would execute trades")

if __name__ == "__main__":
    asyncio.run(main())
