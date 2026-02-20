#!/usr/bin/env python3
"""Web-based Prediction EngineUses Tavily for deep research via skill script."""

import json
import subprocess
import re
from typing import Dict, List, Optional


class WebPredictor:
    """Search web and make predictions."""
    
    def __init__(self):
        self.cache = {}
        self.skill_dir = "/home/clawd/.openclaw/workspace/skills/tavily-search"
        
    async def predict(self, market_question: str, category: str) -> Dict:
        """Make prediction using Tavily."""
        cache_key = f"{market_question}_{category}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        query = self._build_query(market_question, category)
        
        # Call Tavily
        result = self._search(query)
        
        # Parse results
        prediction = self._parse_results(result, market_question)
        self.cache[cache_key] = prediction
        return prediction
        
    def _search(self, query: str) -> str:
        """Run Tavily search."""
        try:
            result = subprocess.run(
                ["node", f"{self.skill_dir}/scripts/search.mjs", query, "--deep", "-n", "5"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception as e:
            print(f"Search error: {e}")
            return ""
    
    def _build_query(self, question: str, category: str) -> str:
        """Build search query."""
        query = question.lower()
        for word in ["will", "by", "the", "in", "on", "if", "?", "$", "%"]:
            query = query.replace(word, " ")
        
        context = {
            "crypto": "price prediction forecast 2026",
            "politics": "polls odds prediction",
            "sports": "odds prediction",
            "technology": "forecast"
        }
        
        if category in context:
            query += f" {context[category]}"
        
        return query.strip()[:100]
    
    def _parse_results(self, text: str, question: str) -> Dict:
        """Parse Tavily markdown output."""
        if not text:
            return {
                "prob_yes": 0.5,
                "confidence": 0.0,
                "reasoning": "No search results",
                "sentiment": 0.0
            }
        
        # Extract answer section
        answer_match = re.search(r'## Answer\s*(.+?)(?=##|$)', text, re.DOTALL)
        answer = answer_match.group(1).strip()[:500] if answer_match else text[:500]
        
        # Extract sources count
        sources = re.findall(r'- \*\*.+?\*\*', text)
        num_sources = len(sources)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(text)
        
        # Calculate probability
        base_prob = 0.5
        adjustment = sentiment * 0.25
        prob_yes = max(0.05, min(0.95, base_prob + adjustment))
        
        # Calculate confidence
        confidence = min(0.35 + (num_sources * 0.08) + (abs(sentiment) * 0.25), 0.85)
        
        # Build reasoning
        if sentiment > 0.3:
            reasoning = f"Bullish sentiment ({sentiment:+.2f}) from {num_sources} sources"
        elif sentiment < -0.3:
            reasoning = f"Bearish sentiment ({sentiment:+.2f}) from {num_sources} sources"
        else:
            reasoning = f"Mixed sentiment ({sentiment:+.2f}) from {num_sources} sources"
        
        return {
            "prob_yes": round(prob_yes, 2),
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "sentiment": round(sentiment, 2),
            "answer_preview": answer[:150]
        }
    
    def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment: -1.0 to +1.0"""
        text = text.lower()
        
        bullish = ["bull", "bullish", "rally", "surge", "moon", "strong", "higher", 
                  "growth", "confident", "expected", "likely", "yes", "reach", 
                  "target", "predict", "forecast"]
        bearish = ["bear", "bearish", "crash", "dump", "fall", "lower", "weak", 
                  "unlikely", "doubt", "correction", "no", "bearish"]
        
        pos = sum(1 for w in bullish if w in text)
        neg = sum(1 for w in bearish if w in text)
        total = pos + neg
        
        return (pos - neg) / max(total, 1)


if __name__ == "__main__":
    import asyncio
    
    async def test():
        p = WebPredictor()
        result = await p.predict(
            "Will Bitcoin hit $100000 by March 2026?",
            "crypto"
        )
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
