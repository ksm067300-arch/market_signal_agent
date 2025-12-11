import os
from datetime import timedelta

# Symbols to monitor. Multiple pairs are supported.
SYMBOLS = ["BTCUSDT"]

# Market data backends: "binance_ws", "binance_rest", or "mock".
MARKET_DATA_BACKEND = "binance_ws"

# Binance endpoints and timing controls.
BINANCE_REST_BASE_URL = "https://api.binance.com"
BINANCE_STREAM_BASE_URL = "wss://stream.binance.com:9443/stream"
POLL_INTERVAL = timedelta(seconds=2)  # used by REST + mock fallbacks
STREAM_RECONNECT_DELAY = timedelta(seconds=5)

# Trigger thresholds.
MAX_PERCENT_DROP = 0.01
MAX_PERCENT_RISE = 0.01
VOLUME_SPIKE_MULTIPLIER = 1.3

# Context TTL for reusing LLM outputs.
SUMMARY_CACHE_TTL = timedelta(minutes=5)

# LLM provider configuration (default: OpenAI).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
