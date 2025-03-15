import numpy as np
import pandas as pd
import logging

class VolumeProfile:
    def __init__(self, candles):
        self.logger = logging.getLogger()
        self.candles = candles  # Recibe velas para análisis

    def calculate_profile(self):
        df = pd.DataFrame(self.candles)
        price_levels = np.linspace(df["min"].min(), df["max"].max(), 20)  # Dividimos en 20 niveles de precio
        volume_at_levels = np.zeros_like(price_levels)

        for _, row in df.iterrows():
            for i, level in enumerate(price_levels):
                if row["min"] <= level <= row["max"]:
                    volume_at_levels[i] += row["volume"]

        self.poc = price_levels[np.argmax(volume_at_levels)]
        self.vah = price_levels[np.percentile(volume_at_levels, 70, interpolation="nearest")]
        self.val = price_levels[np.percentile(volume_at_levels, 30, interpolation="nearest")]

    def generate_signal(self, price):
        if price < self.val:
            return {"strategy": "volume_profile", "signal": "call", "confidence": 0.8}
        elif price > self.vah:
            return {"strategy": "volume_profile", "signal": "put", "confidence": 0.8}
        return {"strategy": "volume_profile", "signal": None, "confidence": 0.0}
