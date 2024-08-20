# Crypto Trading Strategy

This project provides a simple API for generating buy and sell signals for cryptocurrencies based on technical analysis. It uses moving averages, Relative Strength Index (RSI), and Fibonacci retracement levels to determine the signals.

## Features

- Fetches historical price data for Bitcoin, Ethereum, or Binance Coin from the CoinGecko API.
- Calculates 7-day and 21-day moving averages.
- Calculates the Relative Strength Index (RSI).
- Computes Fibonacci retracement levels.
- Generates buy or sell signals based on technical analysis indicators.

## Endpoints

### `/strategy` (GET)

Returns a buy or sell signal based on the analysis of historical price data.

#### Query Parameters

- `crypto` (optional): The cryptocurrency to analyze. Can be one of `bitcoin`, `ethereum`, or `binancecoin`. Defaults to `bitcoin`.

#### Example Request

```sh
curl -X GET "http://localhost:5010/strategy?crypto=ethereum"
```

## Installation

- Clone the repository:

```
git clone https://github.com/Philipid3s/crypto-trading-strategy.git
cd crypto-trading-strategy
```

- Install the required packages

```
pip install -r requirements.txt
```

- Run the API

```
python app.py
```

