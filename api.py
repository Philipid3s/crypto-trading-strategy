from flask import Flask, request, jsonify
import numpy as np
import requests
import datetime
import config  # Import the config file

app = Flask(__name__)

# Symbol mapping for Binance API
SYMBOL_MAP = {
    'bitcoin': 'BTCUSDT',
    'ethereum': 'ETHUSDT',
    'binancecoin': 'BNBUSDT'
}

def get_historical_price_range(symbol, startTime, endTime, interval='1h', market='spot', environment='live'):
    binance_symbol = SYMBOL_MAP.get(symbol.lower())
    if not binance_symbol:
        raise ValueError("Invalid symbol. Supported symbols are 'bitcoin', 'ethereum', 'binancecoin'.")

    url = config.HISTORICAL_PRICE_RANGE_API_URL  # Use the URL from the config file
    
    params = {
        'user': config.USER_ID,  # Use the user ID from the config file
        'symbol': binance_symbol,
        'startTime': startTime,
        'endTime': endTime,
        'interval': interval,
        'market': market,
        'environment': environment
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data['data']

def calculate_moving_average(prices, period):
    if len(prices) < period:
        return []
    return np.convolve(prices, np.ones(period) / period, mode='valid')

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
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

@app.route('/strategy', methods=['GET'])
def strategy():
    crypto = request.args.get('crypto', default='bitcoin', type=str)
    datetime_param = request.args.get('DateTime', type=str)  # Replacing startTime and endTime with DateTime
    short_ma_period = request.args.get('short_ma_period', default=4, type=int)
    long_ma_period = request.args.get('long_ma_period', default=24, type=int)
    include_rsi = request.args.get('include_rsi', default=False, type=lambda v: v.lower() == 'true')
    rsi_period = request.args.get('rsi_period', default=14, type=int)  # Default RSI period set to 14
    interval = request.args.get('interval', default='1h', type=str)
    
    if not datetime_param:
        return jsonify({"error": "Missing required parameter: 'DateTime'."}), 400

    try:
        # Convert DateTime to endTime (assuming DateTime is in YYYYMMDDHHmm format)
        end_time = datetime.datetime.strptime(datetime_param, "%Y%m%d%H%M")

        # Calculate the start time based on the interval and long moving average period
        if interval == '1h':
            delta = datetime.timedelta(hours=long_ma_period)
        elif interval == '1d':
            delta = datetime.timedelta(days=long_ma_period)
        else:
            return jsonify({"error": "Invalid interval. Supported intervals are '1h' and '1d'."}), 400

        start_time = end_time - delta
        
        # Convert start and end times to the required format (e.g., Unix timestamp or appropriate string)
        start_time_str = start_time.strftime('%Y%m%d%H%M')
        end_time_str = end_time.strftime('%Y%m%d%H%M')
        
        # Use the historical price range endpoint to get data
        prices_data = get_historical_price_range(crypto, start_time_str, end_time_str, interval)
        prices = [float(data['close']) for data in prices_data]
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if len(prices) < max(long_ma_period, rsi_period):
        return jsonify({"error": "Not enough price data to perform calculations"}), 400

    # Calculate moving averages
    ma_short = calculate_moving_average(prices, short_ma_period)
    ma_long = calculate_moving_average(prices, long_ma_period)
    fibonacci_levels = calculate_fibonacci_levels(prices[-short_ma_period:])

    signal = ""
    trigger_price = 0

    if include_rsi:
        rsi = calculate_rsi(prices, rsi_period)
        current_rsi = rsi[-1]

        # Buy/Sell logic with RSI and Moving Averages
        if ma_short.size > 0 and ma_long.size > 0:
            # Buy signal if short MA > long MA and RSI < 30 (oversold condition)
            if ma_short[-1] > ma_long[-1] and current_rsi < 30:
                signal = "buy"
                trigger_price = round(fibonacci_levels["38.2%"])
            # Sell signal if short MA < long MA and RSI > 70 (overbought condition)
            elif ma_short[-1] < ma_long[-1] and current_rsi > 70:
                signal = "sell"
                trigger_price = round(fibonacci_levels["61.8%"])
            else:
                signal = "neutral"
                trigger_price = 0
    else:
        # Buy signal without RSI
        if ma_short.size > 0 and ma_long.size > 0:
            if ma_short[-1] > ma_long[-1]:
                signal = "buy"
                trigger_price = round(fibonacci_levels["38.2%"])
            # Sell signal without RSI
            elif ma_short[-1] < ma_long[-1]:
                signal = "sell"
                trigger_price = round(fibonacci_levels["61.8%"])

    response = {
        "trigger_price": trigger_price,
        "transaction_type": signal
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5010)
