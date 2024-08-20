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

def get_historical_price_data(symbol, startTime, endTime, interval='1h', market='spot', environment='live'):
    # Convert symbol to Binance format
    binance_symbol = SYMBOL_MAP.get(symbol.lower())
    if not binance_symbol:
        raise ValueError("Invalid symbol. Supported symbols are 'bitcoin', 'ethereum', 'binancecoin'.")

    url = config.HISTORICAL_PRICE_API_URL  # Use the URL from the config file
    
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
    response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    data = response.json()
    return data['data']

def calculate_moving_average(prices, period):
    if len(prices) < period:
        return []
    return np.convolve(prices, np.ones(period) / period, mode='valid')

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
    start_time = request.args.get('startTime', type=str)
    end_time = request.args.get('endTime', type=str)
    short_ma_period = request.args.get('short_ma_period', default=4, type=int)
    long_ma_period = request.args.get('long_ma_period', default=24, type=int)
    include_rsi = request.args.get('include_rsi', default=False, type=lambda v: v.lower() == 'true')
    interval = request.args.get('interval', default='1h', type=str)
    
    if not all([crypto, start_time, end_time]):
        return jsonify({"error": "Missing required parameters: 'crypto', 'startTime', 'endTime'."}), 400

    try:
        prices_data = get_historical_price_data(crypto, start_time, end_time, interval)
        prices = [float(data['close']) for data in prices_data]
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if len(prices) < long_ma_period:
        return jsonify({"error": "Not enough price data to perform calculations"}), 400

    ma_short = calculate_moving_average(prices, short_ma_period)
    ma_long = calculate_moving_average(prices, long_ma_period)
    fibonacci_levels = calculate_fibonacci_levels(prices[-short_ma_period:])

    signal = ""
    trigger_price = 0

    if ma_short.size > 0 and ma_long.size > 0:
        # Buy condition without RSI
        if ma_short[-1] > ma_long[-1]:
            signal = "buy"
            trigger_price = round(fibonacci_levels["38.2%"])
        # Sell condition without RSI
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
