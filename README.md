# Crypto Trading Strategy

This project implements a Flask web application that proposes trading transactions based on Bitcoin (BTC) price data analysis. The analysis includes moving averages, Relative Strength Index (RSI), and Fibonacci retracement levels. The application fetches BTC price data from the CoinGecko API and provides buy/sell signals based on the computed indicators.

## Features

- Fetches BTC price data from CoinGecko API.
- Calculates 20-day and 50-day moving averages.
- Calculates RSI with a period of 14.
- Computes Fibonacci retracement levels.
- Provides buy/sell signals based on the computed indicators.

## Endpoints

### `/propose-transaction` (GET)

This endpoint proposes a trading transaction based on BTC price analysis.

#### Query Parameters

- `btc_quantity` (float): The current quantity of BTC held.
- `usdt_amount` (float): The current amount of USDT available.

#### Example Request

http://localhost:5000/propose-transaction?btc_quantity=1.5&usdt_amount=5000

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

