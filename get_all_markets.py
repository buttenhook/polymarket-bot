#!/home/clawd/.openclaw/venvs/trading-bot/bin/python3
"""Get ALL markets - trying different approaches"""
import requests
import json

host = "https://gamma-api.polymarket.com"

def fetch_markets(params):
    """Fetch markets with given params"""
    try:
        r = requests.get(f"{host}/markets", params=params, timeout=15)
        return r.json()
    except Exception as e:
        print(f"Error: {e}")
        return []

def fetch_events():
    """Fetch events"""
    try:
        r = requests.get(f"{host}/events?active=true&limit=100", timeout=15)
        return r.json()
    except Exception as e:
        print(f"Error: {e}")
        return []

print("="*70)
print("METHOD 1: Large limit, no filters")
print("="*70)
markets = fetch_markets({"limit": 200, "active": "true", "order": "volume"})
print(f"Markets: {len(markets)}")
for m in markets[:10]:
    vol = float(m.get('volume', 0) or 0) / 1000
    print(f"  - {m.get('question', '')[:50]}... | Vol: ${vol:.0f}K")

print("\n" + "="*70)
print("METHOD 2: Filter by tag 'sports'")
print("="*70)
sports = fetch_markets({"limit": 100, "active": "true", "tag": "sports"})
print(f"Markets: {len(sports)}")
for m in sports[:5]:
    print(f"  - {m.get('question', '')[:50]}")

print("\n" + "="*70)
print("METHOD 3: Filter by tag 'nba'")
print("="*70)
nba = fetch_markets({"limit": 100, "active": "true", "tag": "nba"})
print(f"Markets: {len(nba)}")
for m in nba[:5]:
    print(f"  - {m.get('question', '')[:50]}")

print("\n" + "="*70)
print("METHOD 4: Filter by tag 'nfl'")
print("="*70)
nfl = fetch_markets({"limit": 100, "active": "true", "tag": "nfl"})
print(f"Markets: {len(nfl)}")
for m in nfl[:5]:
    print(f"  - {m.get('question', '')[:50]}")

print("\n" + "="*70)
print("METHOD 5: All events (not markets)")
print("="*70)
events = fetch_events()
print(f"Events: {len(events)}")
sports_events = [e for e in events if any(t in str(e.get('tags',[])).lower() for t in ['sport', 'nba', 'nfl'])]
print(f"Sports events: {len(sports_events)}")
for e in sports_events[:5]:
    print(f"  - {e.get('title', '')[:50]}")
    for m in e.get('markets', [])[:2]:
        print(f"      -> {m.get('question', '')[:40]}")

print("\n" + "="*70)
print("METHOD 6: Check unique tags in all markets")
print("="*70)
all_markets = fetch_markets({"limit": 300, "active": "true"})
tags = set()
for m in all_markets:
    for t in m.get('tags', []):
        tags.add(t)
print(f"Unique tags found ({len(tags)}):")
for t in sorted(tags):
    print(f"  {t}")
