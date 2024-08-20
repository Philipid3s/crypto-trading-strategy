# Crypto Trading Strategy

This project provides a simple API for generating buy and sell signals for cryptocurrencies based on technical analysis. It uses moving averages, Relative Strength Index (RSI), and Fibonacci retracement levels to determine the signals.

## Features

- Fetch historical price data from Binance.
- Calculate moving averages and RSI for cryptocurrency prices.
- Generate buy/sell signals based on trading strategy logic.
- Include configurable parameters such as moving average periods and intervals.

## Prerequisites

- Python 3.x
- Flask
- NumPy
- Requests
- Moment (via `python-dateutil`)

## Endpoints

### `/strategy` (GET)

Generate buy/sell signals based on the moving averages and RSI strategy.

#### Query Parameters

- `crypto` (required): The cryptocurrency symbol (bitcoin, ethereum, binancecoin).
- `DateTime` (required): Datetime in YYYYMMDDHHmm format for the end time of the price data.
- `short_ma_period` (optional): Short moving average period in hours. Default: 4.
- `long_ma_period` (optional): Long moving average period in hours. Default: 24.
- `include_rsi` (optional): Boolean to include RSI in the strategy calculation (default: true).
- `rsi_period` (optional): The period for RSI calculation (default: 14).
- `interval` (optional): Time interval for price data (default: 1h).

#### Example Request

```bash
http://localhost:5010/strategy?crypto=bitcoin&DateTime=202401020000&short_ma_period=4&long_ma_period=24&interval=1h&include_rsi=true
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

