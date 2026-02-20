#!/usr/bin/env python3
"""
Polymarket AI Trading Bot
Main entry point for automated prediction market trading.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Setup paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from strategies.predictor import MarketAnalyzer
from strategies.risk_manager import RiskManager
from utils.polymarket_api import PolymarketClient
from utils.data_feed import DataAggregator

# Configuration
COFIG_FILE = BASE_DIR / "config" / "settings.json"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PolymarketBot:
    """
    AI-powered prediction market trading bot.
    """
    
    def __init__(self):
        self.client = None
        self.analyzer = MarketAnalyzer()
        self.risk_manager = RiskManager()
        self.data_feed = DataAggregator()
        self.active_positions = {}
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        default_config = {
            "max_trade_size": 50,  # USDC
            "daily_loss_limit": -3,  # R units
            "min_confidence": 0.65,  # 65% confidence threshold
            "max_open_positions": 5,
            "markets_to_track": [
                "politics", "crypto", "sports", "technology"
            ],
            "prediction_model": "ensemble",
            "auto_execute": False,  # Manual approval by default
        }
        
        if COFIG_FILE.exists():
            with open(COFIG_FILE) as f:
                loaded = json.load(f)
                default_config.update(loaded)
        
        return default_config
    
    async def initialize(self):
        """Initialize API connection."""
        logger.info("Initializing Polymarket Bot...")
        
        # Load credentials
        api_key = os.getenv("POLYMARKET_API_KEY")
        api_secret = os.getenv("POLYMARKET_API_SECRET")
        
        if not api_key or not api_secret:
            logger.error("API credentials not found. Set POLYMARKET_API_KEY and POLYMARKET_API_SECRET")
            return False
        
        self.client = PolymarketClient(api_key, api_secret)
        
        try:
            await self.client.connect()
            logger.info("Connected to Polymarket")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def scan_markets(self) -> List[Dict]:
        """
        Scan active markets and return potential opportunities.
        """
        logger.info("Scanning markets...")
        
        opportunities = []
        
        try:
            # Fetch active markets
            markets = await self.client.get_active_markets(
                categories=self.config["markets_to_track"]
            )
            
            for market in markets:
                # Analyze market
                prediction = await self.analyzer.analyze_market(market)
                
                if prediction["confidence"] >= self.config["min_confidence"]:
                    opportunities.append({
                        "market": market,
                        "prediction": prediction,
                        "edge": self._calculate_edge(prediction, market)
                    })
            
            # Sort by edge (highest first)
            opportunities.sort(key=lambda x: x["edge"], reverse=True)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Market scan failed: {e}")
            return []
    
    def _calculate_edge(self, prediction: Dict, market: Dict) -> float:
        """
        Calculate expected edge vs market odds.
        """
        predicted_prob = prediction["probability"]
        market_odds = market.get("yes_price", 0.5)
        
        # Edge = |predicted - market| * confidence
        edge = abs(predicted_prob - market_odds) * prediction["confidence"]
        return edge
    
    async def evaluate_position(self, opportunity: Dict) -> Optional[Dict]:
        """
        Evaluate if we should take a position.
        """
        market = opportunity["market"]
        prediction = opportunity["prediction"]
        
        # Check risk limits
        if len(self.active_positions) >= self.config["max_open_positions"]:
            logger.info("Max positions reached")
            return None
        
        # Check if already in this market
        if market["id"] in self.active_positions:
            return None
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position(
            confidence=prediction["confidence"],
            edge=opportunity["edge"],
            volatility=market.get("volume", 1000)
        )
        
        # Risk check
        if not self.risk_manager.approve_trade(
            position_size,
            prediction["probability"],
            market.get("yes_price", 0.5)
        ):
            return None
        
        return {
            "market_id": market["id"],
            "side": "YES" if prediction["direction"] == "UP" else "NO",
            "size": min(position_size, self.config["max_trade_size"]),
            "confidence": prediction["confidence"],
            "reasoning": prediction["reasoning"]
        }
    
    async def execute_trade(self, decision: Dict):
        """
        Execute trade decision.
        """
        if self.config["auto_execute"]:
            logger.info(f"Executing: {decision}")
            result = await self.client.place_order(
                market_id=decision["market_id"],
                side=decision["side"],
                size=decision["size"]
            )
            
            if result:
                self.active_positions[decision["market_id"]] = decision
                logger.info(f"Trade executed: {result}")
                return result
        else:
            # Log for manual approval
            logger.info(f"TRADE PROPOSED (manual approval required): {json.dumps(decision, indent=2)}")
            return None
    
    async def monitor_positions(self):
        """
        Monitor open positions for exits.
        """
        for market_id, position in list(self.active_positions.items()):
            market = await self.client.get_market(market_id)
            
            if market.get("resolved"):
                del self.active_positions[market_id]
                logger.info(f"Position resolved: {market_id}")
                continue
            
            # Check for exit signals
            current_prediction = await self.analyzer.analyze_market(market)
            
            if current_prediction["confidence"] < 0.5:
                # Confidence dropped, consider exit
                logger.info(f"Exit signal for {market_id}: confidence dropped")
    
    async def run(self):
        """
        Main bot loop.
        """
        logger.info("Bot starting...")
        
        connected = await self.initialize()
        if not connected:
            logger.error("Failed to initialize")
            return
        
        try:
