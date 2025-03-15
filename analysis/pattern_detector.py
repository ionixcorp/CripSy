import logging
import pandas as pd
import talib

class PatternDetector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger()

    def price_action(self, data):
        """S/R con volumen y tendencia (inspirado en Binary King)."""
        latest = data.iloc[-1]
        support = data["min"].rolling(50).min().iloc[-1]
        resistance = data["max"].rolling(50).max().iloc[-1]
        data["sma10"] = talib.SMA(data["close"], timeperiod=10)
        trend = "up" if latest["close"] > data["sma10"].iloc[-1] else "down"
        movement = latest["close"] - latest["open"]
        volume_spike = latest["volume"] > talib.SMA(data["volume"], 20).iloc[-1] * 1.5

        if latest["close"] <= support * 1.001 and movement > self.config.threshold_call and volume_spike:
            return {"strategy": "price_action", "signal": "call", "confidence": 0.75}
        elif latest["close"] >= resistance * 0.999 and movement < self.config.threshold_put and volume_spike:
            return {"strategy": "price_action", "signal": "put", "confidence": 0.75}
        return {"strategy": "price_action", "signal": None, "confidence": 0.0}

    def candle_patterns(self, data):
        """Patrones avanzados (inspirado en Nadex y Pinocho)."""
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        movement = latest["close"] - prev["open"]
        is_hammer = (latest["close"] > latest["open"]) and (latest["min"] < latest["open"] * 0.999) and (latest["max"] - latest["close"] < latest["close"] - latest["open"])
        is_shooting_star = (latest["close"] < latest["open"]) and (latest["max"] > latest["open"] * 1.001) and (latest["close"] - latest["min"] < latest["open"] - latest["close"])
        is_pinocchio = (latest["max"] - max(latest["open"], latest["close"])) > 2 * abs(latest["open"] - latest["close"])

        if is_hammer:
            return {"strategy": "candle_patterns", "signal": "call", "confidence": 0.8}
        elif is_shooting_star or is_pinocchio:
            return {"strategy": "candle_patterns", "signal": "put", "confidence": 0.85}
        return {"strategy": "candle_patterns", "signal": None, "confidence": 0.0}

    def momentum(self, data):
        """RSI y MACD ajustados (inspirado en Nadex)."""
        if len(data) < 35:
            return {"strategy": "momentum", "signal": None, "confidence": 0.0}
        data["rsi"] = talib.RSI(data["close"], timeperiod=5)
        macd, macd_signal, _ = talib.MACD(data["close"], fastperiod=12, slowperiod=26, signalperiod=9)
        data["macd_diff"] = macd - macd_signal
        latest = data.iloc[-1]

        if latest["rsi"] < 35 and latest["macd_diff"] > 0:
            return {"strategy": "momentum", "signal": "call", "confidence": 0.7}
        elif latest["rsi"] > 65 and latest["macd_diff"] < 0:
            return {"strategy": "momentum", "signal": "put", "confidence": 0.7}
        return {"strategy": "momentum", "signal": None, "confidence": 0.0}

    def news_impact(self, data):
        """Placeholder para eventos (inspirado en Soros)."""
        return {"strategy": "news_impact", "signal": None, "confidence": 0.0}

    def analyze(self, data):
        if data is None or data.empty:
            self.logger.warning("⚠️ No hay datos para analizar patrones.")
            return []
        return [
            self.price_action(data),
            self.candle_patterns(data),
            self.momentum(data),
            self.news_impact(data)
        ]