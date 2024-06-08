from flask import Flask, request, jsonify
import numpy as np
import requests

app = Flask(__name__)

# Function to get BTC price data from CoinGecko API
def get_btc_price_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': '50',
        'interval': 'daily'
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = [price[1] for price in data['prices']]
    return prices

def calculate_moving_average(prices, period):
    return np.convolve(prices, np.ones(period) / period, mode='valid')

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
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

@app.route('/propose-transaction', methods=['GET'])
def propose_transaction():
    current_btc_quantity = float(request.args.get('btc_quantity'))
    current_usdt_amount = float(request.args.get('usdt_amount'))

    prices = get_btc_price_data()
    ma_20 = calculate_moving_average(prices, 20)
    ma_50 = calculate_moving_average(prices, 50)
    rsi = calculate_rsi(prices)
    fibonacci_levels = calculate_fibonacci_levels(prices[-50:])  # Last 50 days

    latest_price = prices[-1]
    signal = ""
    trigger_price = 0
    btc_quantity = 0

    if ma_20[-1] > ma_50[-1] and rsi[-1] < 70:
        signal = "buy"
        trigger_price = fibonacci_levels["38.2%"]  # Example of using a Fibonacci level as trigger
        btc_quantity = (current_usdt_amount / latest_price) * 0.1  # Buy up to 10% of available USDT
    elif ma_20[-1] < ma_50[-1] and rsi[-1] > 30:
        signal = "sell"
        trigger_price = fibonacci_levels["61.8%"]  # Example of using a Fibonacci level as trigger
        btc_quantity = current_btc_quantity * 0.1  # Sell up to 10% of current BTC holdings

    response = {
        "trigger_price": trigger_price,
        "btc_quantity": btc_quantity,
        "transaction_type": signal
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
