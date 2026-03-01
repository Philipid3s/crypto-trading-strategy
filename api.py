from flask import Flask, request, jsonify, send_file
import numpy as np
import requests
import datetime
import os
import config  # Import the config file

app = Flask(__name__)

# Symbol mapping for Binance API
SYMBOL_MAP = {
    'bitcoin': 'BTCUSDT',
    'ethereum': 'ETHUSDT',
    'binancecoin': 'BNBUSDT'
}

COINGECKO_ID_MAP = {
    'bitcoin': 'bitcoin',
    'ethereum': 'ethereum',
    'binancecoin': 'binancecoin',
}

INTERVAL_TO_MILLISECONDS = {
    '1h': 60 * 60 * 1000,
    '1d': 24 * 60 * 60 * 1000,
}


def _parse_datetime_to_milliseconds(datetime_str):
    dt = datetime.datetime.strptime(datetime_str, "%Y%m%d%H%M")
    return int(dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)


def _fetch_custom_historical_price_range(symbol, user, startTime, endTime, interval, market, environment):
    binance_symbol = SYMBOL_MAP.get(symbol.lower())
    if not binance_symbol:
        raise ValueError("Invalid symbol. Supported symbols are 'bitcoin', 'ethereum', 'binancecoin'.")

    url = config.CUSTOM_HISTORICAL_PRICE_RANGE_API_URL

    params = {
        'user': user,
        'symbol': binance_symbol,
        'startTime': startTime,
        'endTime': endTime,
        'interval': interval,
        'market': market,
        'environment': environment
    }
    response = requests.get(url, params=params, timeout=config.HISTORICAL_PRICE_TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    if 'data' not in data or not isinstance(data['data'], list):
        raise ValueError("Invalid response from historical price service.")
    return data['data']


def _fetch_binance_historical_price_range(symbol, startTime, endTime, interval):
    binance_symbol = SYMBOL_MAP.get(symbol.lower())
    if not binance_symbol:
        raise ValueError("Invalid symbol. Supported symbols are 'bitcoin', 'ethereum', 'binancecoin'.")

    interval_ms = INTERVAL_TO_MILLISECONDS.get(interval)
    if not interval_ms:
        raise ValueError("Invalid interval for Binance. Supported intervals are '1h' and '1d'.")

    start_ms = _parse_datetime_to_milliseconds(startTime)
    end_ms = _parse_datetime_to_milliseconds(endTime)
    if end_ms <= start_ms:
        raise ValueError("Invalid time range. 'endTime' must be after 'startTime'.")

    all_klines = []
    current_start = start_ms

    while current_start < end_ms:
        params = {
            'symbol': binance_symbol,
            'interval': interval,
            'startTime': current_start,
            'endTime': end_ms,
            'limit': 1000,
        }
        url = f"{config.BINANCE_BASE_URL.rstrip('/')}/api/v3/klines"
        response = requests.get(url, params=params, timeout=config.HISTORICAL_PRICE_TIMEOUT_SECONDS)
        response.raise_for_status()
        klines = response.json()

        if not isinstance(klines, list) or not klines:
            break

        all_klines.extend(klines)
        last_open_time = int(klines[-1][0])
        next_start = last_open_time + interval_ms
        if next_start <= current_start:
            break
        current_start = next_start

    if not all_klines:
        raise ValueError("No Binance price data returned for the requested range.")

    return [
        {
            'close': kline[4],
            'high': kline[2],
            'low': kline[3],
            'openTime': kline[0],
        }
        for kline in all_klines
    ]


def _bucket_coingecko_prices(prices, interval):
    interval_ms = INTERVAL_TO_MILLISECONDS.get(interval)
    if not interval_ms:
        raise ValueError("Invalid interval for CoinGecko. Supported intervals are '1h' and '1d'.")

    buckets = {}
    for point in prices:
        if not isinstance(point, list) or len(point) < 2:
            continue
        timestamp_ms = int(point[0])
        price = float(point[1])
        bucket_ts = (timestamp_ms // interval_ms) * interval_ms

        if bucket_ts not in buckets:
            buckets[bucket_ts] = {'open': price, 'high': price, 'low': price, 'close': price}
        else:
            bucket = buckets[bucket_ts]
            bucket['high'] = max(bucket['high'], price)
            bucket['low'] = min(bucket['low'], price)
            bucket['close'] = price

    if not buckets:
        return []

    return [
        {
            'close': bucket['close'],
            'high': bucket['high'],
            'low': bucket['low'],
            'openTime': ts,
        }
        for ts, bucket in sorted(buckets.items(), key=lambda item: item[0])
    ]


def _fetch_coingecko_historical_price_range(symbol, startTime, endTime, interval):
    coin_id = COINGECKO_ID_MAP.get(symbol.lower())
    if not coin_id:
        raise ValueError("Invalid symbol. Supported symbols are 'bitcoin', 'ethereum', 'binancecoin'.")

    start_seconds = _parse_datetime_to_milliseconds(startTime) // 1000
    end_seconds = _parse_datetime_to_milliseconds(endTime) // 1000
    if end_seconds <= start_seconds:
        raise ValueError("Invalid time range. 'endTime' must be after 'startTime'.")

    url = f"{config.COINGECKO_BASE_URL.rstrip('/')}/coins/{coin_id}/market_chart/range"
    headers = {}
    if config.COINGECKO_DEMO_API_KEY:
        headers['x-cg-demo-api-key'] = config.COINGECKO_DEMO_API_KEY

    params = {
        'vs_currency': config.COINGECKO_VS_CURRENCY,
        'from': start_seconds,
        'to': end_seconds,
        'precision': 'full',
    }
    response = requests.get(
        url,
        params=params,
        headers=headers if headers else None,
        timeout=config.HISTORICAL_PRICE_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    prices = data.get('prices')
    if not isinstance(prices, list):
        raise ValueError("Invalid response from CoinGecko: missing 'prices'.")

    bucketed = _bucket_coingecko_prices(prices, interval)
    if not bucketed:
        raise ValueError("No CoinGecko price data returned for the requested range.")
    return bucketed


def get_historical_price_range(
    symbol,
    user,
    startTime,
    endTime,
    interval='1h',
    market='spot',
    environment='live',
):
    provider = config.MARKET_DATA_PROVIDER.lower()
    if provider == 'custom':
        return _fetch_custom_historical_price_range(symbol, user, startTime, endTime, interval, market, environment)
    if provider == 'coingecko':
        return _fetch_coingecko_historical_price_range(symbol, startTime, endTime, interval)
    if provider == 'binance':
        return _fetch_binance_historical_price_range(symbol, startTime, endTime, interval)
    raise ValueError("Invalid MARKET_DATA_PROVIDER. Supported values: 'binance', 'coingecko', 'custom'.")

def calculate_moving_average(prices, period):
    if len(prices) < period:
        return []
    return np.convolve(prices, np.ones(period) / period, mode='valid')

def calculate_rsi(prices, period=14):
    if len(prices) <= period:
        return np.array([])

    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    if down == 0 and up == 0:
        rs = 1
    elif down == 0:
        rs = np.inf
    else:
        rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]  # Change from the previous price
        if delta > 0:
            up_val = delta
            down_val = 0.
        else:
            up_val = 0.
            down_val = -delta

        up = (up * (period - 1) + up_val) / period
        down = (down * (period - 1) + down_val) / period

        if down == 0 and up == 0:
            rs = 1
        elif down == 0:
            rs = np.inf
        else:
            rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi

def calculate_fibonacci_levels(prices):
    high = max(prices)
    low = min(prices)
    diff = high - low
    levels = {
        "0%": high,
        "23.6%": high - 0.236 * diff,
        "38.2%": high - 0.382 * diff,
        "50%": high - 0.5 * diff,
        "61.8%": high - 0.618 * diff,
        "100%": low
    }
    return levels


def calculate_atr(highs, lows, closes, period=14):
    if len(closes) <= period or len(highs) != len(lows) or len(lows) != len(closes):
        return np.array([])

    true_ranges = []
    for i in range(1, len(closes)):
        high_low = highs[i] - lows[i]
        high_prev_close = abs(highs[i] - closes[i - 1])
        low_prev_close = abs(lows[i] - closes[i - 1])
        true_ranges.append(max(high_low, high_prev_close, low_prev_close))

    return calculate_moving_average(np.array(true_ranges), period)


def validate_periods(short_ma_period, long_ma_period, rsi_period, fib_lookback, atr_period):
    if short_ma_period <= 0 or long_ma_period <= 0 or rsi_period <= 0 or fib_lookback <= 1 or atr_period <= 0:
        raise ValueError("Periods must be positive integers, and fib_lookback must be greater than 1.")
    if short_ma_period > long_ma_period:
        raise ValueError("'short_ma_period' cannot be greater than 'long_ma_period'.")


def build_risk_plan(signal, entry_price, atr_value, atr_multiplier, risk_reward):
    if signal == "buy":
        stop_loss = entry_price - (atr_multiplier * atr_value)
        take_profit = entry_price + (risk_reward * (entry_price - stop_loss))
    elif signal == "sell":
        stop_loss = entry_price + (atr_multiplier * atr_value)
        take_profit = entry_price - (risk_reward * (stop_loss - entry_price))
    else:
        return {
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "risk_reward": risk_reward,
        }

    return {
        "entry_price": round(float(entry_price), 4),
        "stop_loss": round(float(stop_loss), 4),
        "take_profit": round(float(take_profit), 4),
        "risk_reward": risk_reward,
    }


def generate_signal(
    prices,
    highs,
    lows,
    short_ma_period,
    long_ma_period,
    include_rsi,
    rsi_period,
    fib_lookback,
    atr_period,
    atr_multiplier,
    risk_reward,
):
    if len(prices) < max(long_ma_period + 2, rsi_period + 2, fib_lookback, atr_period + 1):
        raise ValueError("Not enough price data to perform calculations")

    ma_short = calculate_moving_average(prices, short_ma_period)
    ma_long = calculate_moving_average(prices, long_ma_period)
    fibonacci_levels = calculate_fibonacci_levels(prices[-fib_lookback:])
    atr = calculate_atr(highs, lows, prices, atr_period)
    current_atr = float(atr[-1]) if atr.size > 0 else 0.0

    signal = "neutral"
    trigger_price = 0.0

    if ma_short.size < 2 or ma_long.size < 2:
        return {
            "signal": signal,
            "trigger_price": trigger_price,
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "risk_reward": risk_reward,
            "atr": round(current_atr, 4),
        }

    prev_short = ma_short[-2]
    prev_long = ma_long[-2]
    curr_short = ma_short[-1]
    curr_long = ma_long[-1]

    bullish_crossover = prev_short <= prev_long and curr_short > curr_long
    bearish_crossover = prev_short >= prev_long and curr_short < curr_long

    if include_rsi:
        rsi = calculate_rsi(prices, rsi_period)
        if rsi.size == 0:
            return {
                "signal": signal,
                "trigger_price": trigger_price,
                "entry_price": None,
                "stop_loss": None,
                "take_profit": None,
                "risk_reward": risk_reward,
                "atr": round(current_atr, 4),
            }
        current_rsi = rsi[-1]

        # Trend-following regime with momentum confirmation.
        if bullish_crossover and current_rsi > 50:
            signal = "buy"
            trigger_price = float(fibonacci_levels["38.2%"])
        elif bearish_crossover and current_rsi < 50:
            signal = "sell"
            trigger_price = float(fibonacci_levels["61.8%"])
    else:
        if bullish_crossover:
            signal = "buy"
            trigger_price = float(fibonacci_levels["38.2%"])
        elif bearish_crossover:
            signal = "sell"
            trigger_price = float(fibonacci_levels["61.8%"])

    entry_price = float(prices[-1]) if signal in ("buy", "sell") else None
    if signal in ("buy", "sell"):
        if current_atr <= 0:
            current_atr = max(entry_price * 0.005, 1e-8)
        risk_plan = build_risk_plan(signal, entry_price, current_atr, atr_multiplier, risk_reward)
    else:
        risk_plan = build_risk_plan(signal, 0.0, 0.0, atr_multiplier, risk_reward)

    return {
        "signal": signal,
        "trigger_price": round(trigger_price, 4),
        "entry_price": risk_plan["entry_price"],
        "stop_loss": risk_plan["stop_loss"],
        "take_profit": risk_plan["take_profit"],
        "risk_reward": risk_plan["risk_reward"],
        "atr": round(current_atr, 4),
    }

@app.route('/', methods=['GET'])
def index():
    return send_file('index.html')


@app.route('/strategy', methods=['GET'])
def strategy():
    crypto = request.args.get('crypto', default='bitcoin', type=str)
    user = request.args.get('user', default='1', type=str)
    datetime_param = request.args.get('DateTime', type=str)  # Replacing startTime and endTime with DateTime
    short_ma_period = request.args.get('short_ma_period', default=4, type=int)
    long_ma_period = request.args.get('long_ma_period', default=24, type=int)
    include_rsi = request.args.get('include_rsi', default=False, type=lambda v: v.lower() == 'true')
    rsi_period = request.args.get('rsi_period', default=14, type=int)  # Default RSI period set to 14
    interval = request.args.get('interval', default='1h', type=str)
    fib_lookback = request.args.get('fib_lookback', default=config.FIBONACCI_LOOKBACK_BARS, type=int)
    warmup_bars = request.args.get('warmup_bars', default=config.WARMUP_BARS, type=int)
    atr_period = request.args.get('atr_period', default=config.ATR_PERIOD, type=int)
    atr_multiplier = request.args.get('atr_multiplier', default=config.ATR_MULTIPLIER, type=float)
    risk_reward = request.args.get('risk_reward', default=config.RISK_REWARD_RATIO, type=float)
    
    if not datetime_param:
        return jsonify({"error": "Missing required parameter: 'DateTime'."}), 400

    try:
        validate_periods(short_ma_period, long_ma_period, rsi_period, fib_lookback, atr_period)
        if warmup_bars < 0:
            raise ValueError("'warmup_bars' cannot be negative.")
        if atr_multiplier <= 0 or risk_reward <= 0:
            raise ValueError("'atr_multiplier' and 'risk_reward' must be positive numbers.")

        # Convert DateTime to endTime (assuming DateTime is in YYYYMMDDHHmm format)
        end_time = datetime.datetime.strptime(datetime_param, "%Y%m%d%H%M")

        # Pull additional lookback bars for indicator warmup and more robust levels.
        required_bars = max(
            long_ma_period + 2 + warmup_bars,
            rsi_period + 2 + warmup_bars,
            fib_lookback + warmup_bars,
            atr_period + 1 + warmup_bars,
        )

        if interval == '1h':
            delta = datetime.timedelta(hours=required_bars)
        elif interval == '1d':
            delta = datetime.timedelta(days=required_bars)
        else:
            return jsonify({"error": "Invalid interval. Supported intervals are '1h' and '1d'."}), 400

        start_time = end_time - delta
        
        # Convert start and end times to the required format (e.g., Unix timestamp or appropriate string)
        start_time_str = start_time.strftime('%Y%m%d%H%M')
        end_time_str = end_time.strftime('%Y%m%d%H%M')
        
        # Use the historical price range endpoint to get data
        prices_data = get_historical_price_range(crypto, user, start_time_str, end_time_str, interval)
        prices = [float(data['close']) for data in prices_data]
        highs = [float(data.get('high', data['close'])) for data in prices_data]
        lows = [float(data.get('low', data['close'])) for data in prices_data]

        strategy_result = generate_signal(
            prices,
            highs,
            lows,
            short_ma_period,
            long_ma_period,
            include_rsi,
            rsi_period,
            fib_lookback,
            atr_period,
            atr_multiplier,
            risk_reward,
        )
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch historical prices: {str(e)}"}), 502
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    response = {
        "trigger_price": strategy_result["trigger_price"],
        "transaction_type": strategy_result["signal"],
        "entry_price": strategy_result["entry_price"],
        "stop_loss": strategy_result["stop_loss"],
        "take_profit": strategy_result["take_profit"],
        "risk_reward": strategy_result["risk_reward"],
        "atr": strategy_result["atr"],
    }

    return jsonify(response)

if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, port=5010)
