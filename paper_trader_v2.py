#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""
Paper Trading Mode for Polymarket
Predicts + tracks outcomes, no real money risk.
"""

import sqlite3
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from utils.polymarket_api import PolymarketClient
from utils.tavily_predictor import WebPredictor

PAPER_DB = Path(__file__).parent / "data" / "paper_trades.sqlite"

class PaperTrader:
    """
    Paper trading bot for Polymarket.
    """
    
    def __init__(self):
        self.client = PolymarketClient()
        self.predictor = WebPredictor()
        self.db = self._init_db()
        self.current_year = datetime.now(timezone.utc).year
        
    def _init_db(self) -> sqlite3.Connection:
        """Initialize paper trading database"""
        PAPER_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(PAPER_DB))
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS paper_predictions (
                id INTEGER PRIMARY KEY,
                market_id TEXT NOT NULL,
                question TEXT,
                category TEXT,
                our_prediction REAL,
                market_odds REAL,
                direction TEXT,
                confidence REAL,
                edge REAL,
                sentiment_score REAL,
                reasoning TEXT,
                trade_size REAL,
                open_time TEXT,
                resolve_time TEXT,
                outcome TEXT,
                resolved_value REAL,
                pnl REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        return conn
    
    async def scan_and_predict(self, max_markets: int = 100, days_ahead: int = 30):
        """
        Scan markets, make predictions, log paper trades.
        Filters by date AND year in question to avoid stale markets.
        """
        print(f"\n{'='*60}")
        print("PAPER TRADING SCAN")
        print(f"Year: {self.current_year} | Max days ahead: {days_ahead}")
        print(f"{'='*60}")
        
        # Fetch events (correct endpoint for live data)
        events = await self.client.get_events(active=True, limit=max_markets)
        
        # Flatten events into markets
        markets = []
        for event in events:
            event_markets = event.get("markets", [])
            for market in event_markets:
                market["event_title"] = event.get("title", "")
                market["event_end_date"] = event.get("endDate", "")
                markets.append(market)
        
        print(f"Scanned {len(events)} events ({len(markets)} total markets)")
        
        predictions = []
        skipped_date = 0
        skipped_year = 0
        
        for market in markets:
            pred = await self._analyze_market(market, days_ahead)
            if pred == "SKIPPED_DATE":
                skipped_date += 1
            elif pred == "SKIPPED_YEAR":
                skipped_year += 1
            elif pred:
                predictions.append(pred)
        
        print(f"\nFiltered: {skipped_date} (past date), {skipped_year} (past year)")
        
        self._log_predictions(predictions)
        self._show_predictions(predictions)
        
        return predictions
    
    async def _analyze_market(self, market: Dict, days_ahead: int) -> Optional[Dict]:
        """
        Analyze single market with AI.
        Returns None if no trade, 'SKIPPED_DATE'/'SKIPPED_YEAR' if filtered.
        """
        question = market.get("question", "")
        market_id = market.get("id", "")
        
        # Check end date is in the future and within range
        end_date = market.get("endDate") or market.get("event_end_date", "")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                
                if end_dt < now:
                    print(f"    Skipping (ended {end_date[:10]}): {question[:40]}...")
                    return "SKIPPED_DATE"
                
                days_until = (end_dt - now).days
                if days_until > days_ahead:
                    return None  # Too far out, silently skip
                    
            except:
                pass
        
        # Check year in question isn't past
        years_in_q = re.findall(r'20\d\d', question)
        for year_str in years_in_q:
            year = int(year_str)
            if year < self.current_year:
                print(f"    Skipping (year {year}): {question[:40]}...")
                return "SKIPPED_YEAR"
        
        # Get current market odds
        prices = market.get("prices", {})
        yes_price = prices.get("yes", 0.5)
        
        try:
            category = self._detect_category(question)
            prediction = await self.predictor.predict(question, category)
        except Exception as e:
            print(f"Prediction failed: {e}")
            return None
        
        our_prob = prediction.get("prob_yes", 0.5)
        edge = abs(our_prob - yes_price)
        confidence = prediction.get("confidence", 0)
        
        if edge < 0.10 or confidence < 0.65:
            return None
        
        direction = "YES" if our_prob > yes_price else "NO"
        trade_size = 10 + (confidence * 40)
        
        return {
            "market_id": market_id,
            "question": question,
            "category": category,
            "our_prediction": our_prob,
            "market_odds": yes_price,
            "direction": direction,
            "confidence": confidence,
            "edge": edge,
            "sentiment_score": prediction.get("sentiment", 0),
            "reasoning": prediction.get("reasoning", "")[:100],
            "trade_size": round(trade_size, 2),
            "open_time": datetime.now(timezone.utc).isoformat()
        }
    
    def _detect_category(self, question: str) -> str:
        """Detect market category"""
        q = question.lower()
        if any(word in q for word in ["bitcoin", "btc", "crypto", "ethereum"]):
            return "crypto"
        elif any(word in q for word in ["trump", "biden", "election", "senate"]):
            return "politics"
        elif any(word in q for word in ["super bowl", "nba", "nfl", "championship"]):
            return "sports"
        else:
            return "other"
    
    def _log_predictions(self, predictions: List[Dict]):
        """Log to database"""
        cursor = self.db.cursor()
        for p in predictions:
            cursor.execute("""
                INSERT INTO paper_predictions (
                    market_id, question, category, our_prediction,
                    market_odds, direction, confidence, edge,
                    sentiment_score, reasoning, trade_size, open_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["market_id"], p["question"], p["category"],
                p["our_prediction"], p["market_odds"], p["direction"],
                p["confidence"], p["edge"], p["sentiment_score"],
                p["reasoning"], p["trade_size"], p["open_time"]
            ))
        self.db.commit()
        print(f"\n💾 Logged {len(predictions)} predictions")
    
    def _show_predictions(self, predictions: List[Dict]):
        """Display predictions"""
        if not predictions:
            print("\nNo