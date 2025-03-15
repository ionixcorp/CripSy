import talib
import numpy as np
import pandas as pd

def get_price_action_signal(data):
    try:
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_cols):
            return "neutral", 0.0

        open_prices = data['open'].astype(np.float64).values
        high_prices = data['high'].astype(np.float64).values
        low_prices = data['low'].astype(np.float64).values
        close_prices = data['close'].astype(np.float64).values

        hammer = talib.CDLHAMMER(open_prices, high_prices, low_prices, close_prices)
        engulfing = talib.CDLENGULFING(open_prices, high_prices, low_prices, close_prices)
        
        recent_hammer = hammer[-5:]
        recent_engulfing = engulfing[-5:]
        
        score = 0.0
        signal = "neutral"
        if any(recent_hammer > 0):
            score += 0.8
            signal = "call"
        if any(recent_engulfing < 0):
            score += 0.8
            signal = "put"
        
        if any(recent_hammer > 0) and any(recent_engulfing < 0):
            signal = "neutral"
            score = 0.0
        
        return signal, score
    except Exception:
        return "neutral", 0.0