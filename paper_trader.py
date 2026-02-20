#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""
Paper Trading Mode for Polymarket
Predicts + tracks outcomes, no real money risk.
"""

import sqlite3
import asyncio
import json
from datetime import datetime, timedelta
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
    
    async def scan_and_predict(self, max_markets: int = 100):
        """Scan markets, make predictions, log paper trades."""
        print(f"\n{'='*60}")
        print("PAPER TRADING SCAN")
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
        
        print(f"Found {len(events)} events ({len(markets)} markets)")
        
        predictions = []
        for market in markets:
            pred = await self._analyze_market(market)
            if pred:
                predictions.append(pred)
        
        self._log_predictions(predictions)
        self._show_predictions(predictions)
        
        return predictions
    
    async def _analyze_market(self, market: Dict) -> Optional[Dict]:
        """Analyze single market with AI."""
        from datetime import datetime, timezone
        
        question = market.get("question", "")
        market_id = market.get("id", "")
        
        # Check end date is in the future
        end_date = market.get("endDate", "")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                if end_dt < datetime.now(timezone.utc):
                    print(f"    Skipping (ended): {question[:40]}...")
                    return None
            except:
                pass
        
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
            "open_time": datetime.now().isoformat()
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
            print("\nNo predictions met threshold")
            return
        
        print(f"\n{'='*60}")
        print(f"PAPER TRADES: {len(predictions)}")
        print(f"{'='*60}")
        
        for i, p in enumerate(predictions, 1):
            print(f"\n{i}. {p['question'][:55]}...")
            print(f"   📊 {p['direction']} @ {p['our_prediction']*100:.0f}% (market: {p['market_odds']*100:.0f}%)")
            print(f"   💰 Paper: ${p['trade_size']:.0f} | Edge: {p['edge']*100:.0f}%")
    
    def get_stats(self) -> Dict:
        """Get paper trading stats"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                COALESCE(COUNT(*), 0) as total,
                COALESCE(SUM(CASE WHEN outcome='WIN' THEN 1 ELSE 0 END), 0) as wins,
                COALESCE(SUM(CASE WHEN outcome='LOSS' THEN 1 ELSE 0 END), 0) as losses,
                COALESCE(SUM(pnl), 0) as total_pnl
            FROM paper_predictions
            WHERE outcome IS NOT NULL
        """)
        row = cursor.fetchone()
        
        total, wins, losses, pnl = row
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        
        return {
            "total_predictions": total or 0,
            "wins": wins or 0,
            "losses": losses or 0,
            "win_rate": win_rate,
            "total_pnl": pnl or 0
        }


async def main():
    """Run paper trading scan"""
    trader = PaperTrader()
    
    print("\n" + "="*60)
    print("PAPER TRADING BOT")
    print("No real money - safe testing mode")
    print("="*60)
    
    # Scan and predict
    predictions = await trader.scan_and_predict(max_markets=5)
    
    # Show stats
    stats = trader.get_stats()
    if stats["total_predictions"] > 0:
        print(f"\n{'='*60}")
        print("HISTORICAL STATS")
        print(f"{'='*60}")
        print(f"Trades: {stats['total_predictions']}")
        print(f"Win Rate: {stats['win_rate']:.1f}%")
        print(f"P&L: ${stats['total_pnl']:.2f}")
    
    print(f"\n✅ Paper trades logged to: {PAPER_DB}")
    print("Run daily to track predictions vs outcomes")


if __name__ == "__main__":
    asyncio.run(main())
