# Crypto Trading Strategy

This project provides a Flask API that generates `buy`, `sell`, or `neutral` signals for supported cryptocurrencies using moving-average crossover events, optional RSI confirmation, Fibonacci retracement levels, and ATR-based risk planning.

## Features

- Fetch historical price data from Binance, CoinGecko, or a custom endpoint.
- Calculate moving averages and RSI for price series.
- Generate deterministic trading output:
  - `transaction_type`: `buy` | `sell` | `neutral`
  - `trigger_price`: decimal price or `0` for neutral
  - `entry_price`, `stop_loss`, `take_profit`, `risk_reward`, `atr`
- Validate strategy periods and request inputs.
- Configure API URL and request timeout via environment variables.

## Prerequisites

- Python 3.10+
- Dependencies in `requirements.txt`

## Configuration

Environment variables:

- `MARKET_DATA_PROVIDER` (default: `binance`)  
  - Supported: `binance`, `coingecko`, `custom`
- `BINANCE_BASE_URL` (default: `https://api.binance.com`)
- `COINGECKO_BASE_URL` (default: `https://api.coingecko.com/api/v3`)
- `COINGECKO_DEMO_API_KEY` (optional)
- `COINGECKO_VS_CURRENCY` (default: `usd`)
- `CUSTOM_HISTORICAL_PRICE_RANGE_API_URL` (default: `http://localhost:3000/historical-price-range`)  
  - Used only when `MARKET_DATA_PROVIDER=custom`
- `HISTORICAL_PRICE_TIMEOUT_SECONDS` (default: `10`)
- `WARMUP_BARS` (default: `100`)
- `FIBONACCI_LOOKBACK_BARS` (default: `50`)
- `ATR_PERIOD` (default: `14`)
- `ATR_MULTIPLIER` (default: `1.5`)
- `RISK_REWARD_RATIO` (default: `2.0`)
- `FLASK_DEBUG` (default: `false`)

## Endpoint

### `/` (GET)

Loads the web dashboard UI for running strategy requests interactively.

### `/strategy` (GET)

Generate buy/sell/neutral signals based on MA crossover events and optional RSI confirmation.

#### Query Parameters

- `crypto` (optional): `bitcoin`, `ethereum`, `binancecoin` (default: `bitcoin`)
- `user` (optional): user id passed through to historical price service (default: `1`)
- `DateTime` (required): end datetime in `YYYYMMDDHHmm` format
- `short_ma_period` (optional): short moving average period (default: `4`)
- `long_ma_period` (optional): long moving average period (default: `24`)
- `include_rsi` (optional): `true`/`false` to include RSI logic (default: `false`)
- `rsi_period` (optional): RSI period (default: `14`)
- `fib_lookback` (optional): bars used for Fibonacci levels (default from config, `50`)
- `warmup_bars` (optional): extra bars fetched for indicator warmup (default from config, `100`)
- `atr_period` (optional): ATR period for risk planning (default from config, `14`)
- `atr_multiplier` (optional): ATR multiplier for stop distance (default from config, `1.5`)
- `risk_reward` (optional): take-profit distance ratio vs stop distance (default from config, `2.0`)
- `interval` (optional): `1h` or `1d` (default: `1h`)

Validation rules:

- All periods must be positive integers.
- `short_ma_period` must be less than or equal to `long_ma_period`.
- `atr_multiplier` and `risk_reward` must be positive.
- Response is `400` for invalid input and `502` when upstream historical price fetch fails.

### Data Provider Notes

- `binance`: Uses public endpoint `GET /api/v3/klines` for OHLC candles.
- `coingecko`: Uses public endpoint `GET /coins/{id}/market_chart/range`, then buckets raw prices into `1h` or `1d` candles.
- `custom`: Uses your existing endpoint contract at `CUSTOM_HISTORICAL_PRICE_RANGE_API_URL`.

#### Response Fields

- `transaction_type`: `buy`, `sell`, or `neutral`
- `trigger_price`: Fibonacci-derived trigger level
- `entry_price`: latest close price on signal, else `null`
- `stop_loss`: ATR-based stop level, else `null`
- `take_profit`: ATR and risk-reward based target, else `null`
- `risk_reward`: configured risk-reward ratio
- `atr`: latest ATR used in risk plan

#### Example Request

```bash
http://localhost:5010/strategy?crypto=bitcoin&DateTime=202603011430&short_ma_period=4&long_ma_period=24&interval=1h&include_rsi=true
```

Use a recent `DateTime` value in `YYYYMMDDHHmm` format (replace the example above with your current target time).

## Installation and Run

```bash
git clone https://github.com/Philipid3s/crypto-trading-strategy.git
cd crypto-trading-strategy
pip install -r requirements.txt
python api.py
```

Then open:

```bash
http://localhost:5010/
```

