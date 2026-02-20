#!/usr/bin/env python3
"""
Daily Paper Trader Scheduler
Runs paper_trader.py once per day and logs results.
"""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
import sqlite3

SCHEDULE_LOG = Path(__file__).parent / "data" / "scheduler.log"
PAPER_DB = Path(__file__).parent / "data" / "paper_trades.sqlite"

def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    
    # Append to log file
    SCHEDULE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULE_LOG, "a") as f:
        f.write(line + "\n")

async def run_paper_trader():
    """Execute paper trader and capture results"""
    log("Starting paper trader run...")
    
    try:
        # Run paper_trader.py
        result = subprocess.run(
            ["python3", str(Path(__file__).parent / "paper_trader.py")],
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout
        )
        
        # Log output
        if result.stdout:
            log("Output:\n" + result.stdout[:2000])  # First 2000 chars
        
        if result.returncode != 0 and result.stderr:
            log(f"Errors: {result.stderr[:500]}")
        
        # Get stats
        stats = await get_stats()
        log(f"Total predictions: {stats['total']}")
        log(f"Win rate: {stats['win_rate']:.1f}%" if stats['resolved'] > 0 else "No resolved yet")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        log("ERROR: Paper trader timed out")
        return False
    except Exception as e:
        log(f"ERROR: {e}")
        return False

async def get_stats():
    """Get current stats from database"""
    try:
        conn = sqlite3.connect(str(PAPER_DB))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN outcome IS NOT NULL THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN outcome='WIN' THEN 1 ELSE 0 END) as wins
            FROM paper_predictions
        """)
        row = cursor.fetchone()
        
        total, resolved, wins = row if row else (0, 0, 0)
        win_rate = (wins / max(resolved, 1) * 100) if resolved > 0 else 0
        
        return {
            "total": total or 0,
            "resolved": resolved or 0,
            "wins": wins or 0,
            "win_rate": win_rate
        }
    except:
        return {"total": 0, "resolved": 0, "wins": 0, "win_rate": 0}

async def main():
    """Main scheduler loop"""
    log("="*60)
    log("DAILY PAPER TRADER SCHEDULER")
    log("="*60)
    
    # Run once now
    await run_paper_trader()
    
    log("Run complete. Set up cron for daily execution:")
    log("  crontab -e")
    log("  0 9 * * * cd /home/clawd/polymarket-bot && python3 scheduler.py")

if __name__ == "__main__":
    asyncio.run(main())
