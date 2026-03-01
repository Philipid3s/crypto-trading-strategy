import math

import pytest

from api import calculate_rsi, generate_signal, validate_periods


def test_validate_periods_accepts_valid_values():
    validate_periods(4, 24, 14, 50, 14)


@pytest.mark.parametrize(
    "short_ma,long_ma,rsi",
    [
        (0, 24, 14),
        (4, 0, 14),
        (4, 24, 0),
        (-1, 24, 14),
    ],
)
def test_validate_periods_rejects_non_positive_values(short_ma, long_ma, rsi):
    with pytest.raises(ValueError, match="positive integers"):
        validate_periods(short_ma, long_ma, rsi, 50, 14)


def test_validate_periods_rejects_short_greater_than_long():
    with pytest.raises(ValueError, match="cannot be greater"):
        validate_periods(25, 24, 14, 50, 14)


def test_validate_periods_rejects_small_fib_lookback():
    with pytest.raises(ValueError, match="fib_lookback"):
        validate_periods(4, 24, 14, 1, 14)


def test_calculate_rsi_flat_series_is_stable():
    prices = [100.0] * 30
    rsi = calculate_rsi(prices, period=14)

    assert rsi.size == len(prices)
    assert math.isfinite(float(rsi[-1]))
    assert float(rsi[-1]) == pytest.approx(50.0)


def test_generate_signal_buy_on_bullish_crossover_without_rsi():
    prices = [10.0] * 15 + [8.0, 8.0, 8.0, 8.0, 15.0]
    highs = [p + 0.5 for p in prices]
    lows = [p - 0.5 for p in prices]
    result = generate_signal(
        prices=prices,
        highs=highs,
        lows=lows,
        short_ma_period=3,
        long_ma_period=5,
        include_rsi=False,
        rsi_period=14,
        fib_lookback=10,
        atr_period=5,
        atr_multiplier=1.5,
        risk_reward=2.0,
    )

    assert result["signal"] == "buy"
    assert result["trigger_price"] > 0
    assert result["entry_price"] == prices[-1]
    assert result["stop_loss"] < result["entry_price"]
    assert result["take_profit"] > result["entry_price"]


def test_generate_signal_sell_on_bearish_crossover_without_rsi():
    prices = [10.0] * 15 + [12.0, 12.0, 12.0, 12.0, 5.0]
    highs = [p + 0.5 for p in prices]
    lows = [p - 0.5 for p in prices]
    result = generate_signal(
        prices=prices,
        highs=highs,
        lows=lows,
        short_ma_period=3,
        long_ma_period=5,
        include_rsi=False,
        rsi_period=14,
        fib_lookback=10,
        atr_period=5,
        atr_multiplier=1.5,
        risk_reward=2.0,
    )

    assert result["signal"] == "sell"
    assert result["trigger_price"] > 0
    assert result["entry_price"] == prices[-1]
    assert result["stop_loss"] > result["entry_price"]
    assert result["take_profit"] < result["entry_price"]


def test_generate_signal_with_rsi_can_be_neutral_without_crossover():
    prices = [100.0] * 30
    highs = [p + 1 for p in prices]
    lows = [p - 1 for p in prices]
    result = generate_signal(
        prices=prices,
        highs=highs,
        lows=lows,
        short_ma_period=3,
        long_ma_period=5,
        include_rsi=True,
        rsi_period=14,
        fib_lookback=10,
        atr_period=5,
        atr_multiplier=1.5,
        risk_reward=2.0,
    )

    assert result["signal"] == "neutral"
    assert result["trigger_price"] == 0.0
    assert result["entry_price"] is None
    assert result["stop_loss"] is None
    assert result["take_profit"] is None


def test_generate_signal_with_rsi_confirms_buy():
    prices = [10.0] * 15 + [8.0, 8.0, 8.0, 8.0, 15.0]
    highs = [p + 0.5 for p in prices]
    lows = [p - 0.5 for p in prices]
    result = generate_signal(
        prices=prices,
        highs=highs,
        lows=lows,
        short_ma_period=3,
        long_ma_period=5,
        include_rsi=True,
        rsi_period=14,
        fib_lookback=10,
        atr_period=5,
        atr_multiplier=1.5,
        risk_reward=2.0,
    )

    assert result["signal"] == "buy"


def test_generate_signal_with_rsi_confirms_sell():
    prices = [10.0] * 15 + [12.0, 12.0, 12.0, 12.0, 5.0]
    highs = [p + 0.5 for p in prices]
    lows = [p - 0.5 for p in prices]
    result = generate_signal(
        prices=prices,
        highs=highs,
        lows=lows,
        short_ma_period=3,
        long_ma_period=5,
        include_rsi=True,
        rsi_period=14,
        fib_lookback=10,
        atr_period=5,
        atr_multiplier=1.5,
        risk_reward=2.0,
    )

    assert result["signal"] == "sell"


def test_generate_signal_rejects_insufficient_data():
    with pytest.raises(ValueError, match="Not enough price data"):
        generate_signal(
            prices=[1.0, 2.0, 3.0],
            highs=[1.0, 2.0, 3.0],
            lows=[1.0, 2.0, 3.0],
            short_ma_period=3,
            long_ma_period=5,
            include_rsi=False,
            rsi_period=14,
            fib_lookback=10,
            atr_period=5,
            atr_multiplier=1.5,
            risk_reward=2.0,
        )
