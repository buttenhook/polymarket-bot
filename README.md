# Wolf Polymarket AI Bot

AI-powered prediction market trading bot using real-time web search.

## Features

- 🤖 **AI Predictions**: Web search + sentiment analysis
- 📊 **Bayesian Analysis**: Probability calculation with confidence
- 🛡️ **Risk Management**: Position sizing, daily limits
- 🔔 **Notifications**: Telegram alerts for trades
- 📈 **Track Record**: Automatic P&L tracking

## Architecture

```
main.py
├── strategies/
│   ├── predictor.py      # Core prediction engine
│   └── risk_manager.py   # Position/risk management
├── utils/
│   ├── polymarket_api.py # Exchange connection
│   ├── web_predictor.py  # Search-based predictions
│   ├── sentiment.py      # Sentiment analyzer
│   └── data_feed.py      # Market data
└── config/
    └── settings.json     # Bot configuration
```

## How Predictions Work

1. **Scan Markets** → Find active opportunities
2. **Fetch News** → Real-time search for relevant info
3. **Analyze Sentiment** → Positive/negative tone
4. **Calculate Probability** → Bayesian model
5. **Risk Check** → Position size, limits
6. **Execute Trade** → or notify for approval

### Example Flow

```
Market: "Will BTC hit $100k by March 2026?"
Current: $65k, YES odds: 35%

1. Search: "BTC $100k prediction 2026 ETF halving"
2. Find: "4 analysts predict $100k by Feb"
3. Sentiment: +0.65 (strongly positive)
4. Prediction: 62% YES, confidence: 0.71
5. Edge: 62% vs 35% market = 27% edge
6. Trade: YES, $25, confidence HIGH
```

## Setup

### 1. Install Dependencies

```bash
cd ~/polymarket-bot
pip install -r requirements.txt
```

### 2. Set API Keys

```bash
export POLYMARKET_API_KEY="your_key"
export POLYMARKET_API_SECRET="your_secret"
```

### 3. Configure Bot

Edit `config/settings.json`:
- `max_trade_size`: Max USDC per trade
- `min_confidence`: Threshold for trades
- `auto_execute`: false = manual approval

### 4. Run

```bash
python main.py
```

## Trading Strategies

### Momentum (Active)
- **Asset**: MNQ/MES futures
- **Setup**: 8pt/30pt momentum candles
- **Status**: ✅ Validated, +28R (60 days)

### Prediction Markets (New)
- **Source**: Polymarket
- **Edge**: Information asymmetry
- **Timeframe**: Hours to days
- **Risk**: Binary outcomes

## Risk Rules

- Max 5 open positions
- Max $50 per trade
- Stop day at -3R
- 65% minimum confidence
- Manual approval for size >$25

## Performance Tracking

- Win rate by category
- Edge vs market
- P&L by strategy
- Confidence calibration

## Next Steps

1. [ ] Add real web search API
2. [ ] Train sentiment model
3. [ ] Backtest on historical
4. [ ] Deploy to VPS
5. [ ] Monitor results

---

*Built by Wolf | 2026*
