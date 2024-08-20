# Crypto Trading Strategy

This project provides a simple API for generating buy and sell signals for cryptocurrencies based on technical analysis. It uses moving averages, Relative Strength Index (RSI), and Fibonacci retracement levels to determine the signals.

## Features


- **Moving Averages**: Calculate short-term and long-term moving averages to determine buy/sell signals.
- **Customizable Parameters**: Specify the moving average periods, interval (hourly or daily), and whether to include RSI in the strategy.
- **Historical Price Data**: Fetch historical price data from Binance API using configurable parameters.

## Prerequisites

- Python 3.x
- Flask
- Requests
- NumPy
- A valid Binance API URL and user ID

## Endpoints

### `/strategy` (GET)

Description: Get trading strategy recommendations based on historical price data.

#### Query Parameters

- `crypto` (optional): The cryptocurrency to analyze. Can be one of `bitcoin`, `ethereum`, or `binancecoin`. Defaults to `bitcoin`.

- `crypto` (required): Cryptocurrency symbol. Options: bitcoin, ethereum, binancecoin.
- `startTime` (required): Start time in YYYYMMDDHHmm format.
- `endTime` (required): End time in YYYYMMDDHHmm format.
- `short_ma_period` (optional): Short moving average period in hours. Default: 4.
- `long_ma_period` (optional): Long moving average period in hours. Default: 24.
- `interval` (optional): Data interval. Options: 1h (hourly), 1d (daily). Default: 1h.
- `include_rsi` (optional): Whether to include RSI in the strategy. Options: true, false. Default: false.

#### Example Request

```bash
http://localhost:5010/strategy?crypto=bitcoin&startTime=202401010000&endTime=202401020000&short_ma_period=4&long_ma_period=24&interval=1h&include_rsi=false

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

