import talib
import numpy as np

def get_momentum_signal(data):
    try:
        close_prices = data['close'].astype(np.float64).values
        rsi = talib.RSI(close_prices, timeperiod=14)
        macd, macdsignal, _ = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
        
        signal = "neutral"
        score = 0.0
        if rsi[-1] < 30 and macd[-1] > macdsignal[-1]:
            signal = "call"
            score += 0.9
        elif rsi[-1] > 70 and macd[-1] < macdsignal[-1]:
            signal = "put"
            score += 0.9
        
        return signal, score
    except Exception:
        return "neutral", 0.0