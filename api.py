from flask import Flask, request, jsonify
import numpy as np
import requests

app = Flask(__name__)

# Function to get price data from CoinGecko API for a specified cryptocurrency
def get_price_data(crypto):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': '21',
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    data = response.json()
    prices = [price[1] for price in data['prices']]
    return prices

def calculate_moving_average(prices, period):
    if len(prices) < period:
        return []
    return np.convolve(prices, np.ones(period) / period, mode='valid')

def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return []

    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]  # The diff is 1 shorter

        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

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
    if crypto not in ['bitcoin', 'ethereum', 'binancecoin']:
        return jsonify({"error": "Invalid cryptocurrency. Choose from 'bitcoin', 'ethereum', or 'binancecoin'."}), 400
    
    try:
        prices = get_price_data(crypto)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

    if len(prices) < 21:
        return jsonify({"error": "Not enough price data to perform calculations"}), 400

    ma_7 = calculate_moving_average(prices, 7)  # last week
    ma_21 = calculate_moving_average(prices, 21)  # last 3 weeks
    rsi = calculate_rsi(prices)
    fibonacci_levels = calculate_fibonacci_levels(prices[-7:])  # Last 7 days

    signal = ""
    trigger_price = 0

    if ma_7.size > 0 and ma_21.size > 0:
        # Buy condition
        if ma_7[-1] > ma_21[-1] and rsi[-1] < 70:
            signal = "buy"
            trigger_price = round(fibonacci_levels["38.2%"])  # Conservative entry level
        # Sell condition
        elif ma_7[-1] < ma_21[-1] and rsi[-1] > 30:
            signal = "sell"
            trigger_price = round(fibonacci_levels["61.8%"])  # Strong retracement leveler

    response = {
        "trigger_price": trigger_price,
        "transaction_type": signal
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5010)
