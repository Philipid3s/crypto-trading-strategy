import os

# Market data provider: binance | coingecko | custom
MARKET_DATA_PROVIDER = os.getenv("MARKET_DATA_PROVIDER", "binance")

# Custom historical API (used when MARKET_DATA_PROVIDER=custom)
CUSTOM_HISTORICAL_PRICE_RANGE_API_URL = os.getenv(
    "CUSTOM_HISTORICAL_PRICE_RANGE_API_URL",
    "http://localhost:3000/historical-price-range",
)

# Public Binance API
BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")

# Public CoinGecko API
COINGECKO_BASE_URL = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
COINGECKO_DEMO_API_KEY = os.getenv("COINGECKO_DEMO_API_KEY", "")
COINGECKO_VS_CURRENCY = os.getenv("COINGECKO_VS_CURRENCY", "usd")

HISTORICAL_PRICE_TIMEOUT_SECONDS = int(os.getenv("HISTORICAL_PRICE_TIMEOUT_SECONDS", "10"))
WARMUP_BARS = int(os.getenv("WARMUP_BARS", "100"))
FIBONACCI_LOOKBACK_BARS = int(os.getenv("FIBONACCI_LOOKBACK_BARS", "50"))
ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
ATR_MULTIPLIER = float(os.getenv("ATR_MULTIPLIER", "1.5"))
RISK_REWARD_RATIO = float(os.getenv("RISK_REWARD_RATIO", "2.0"))
