import numpy as np
import pandas as pd
import talib
import logging

def extract_features(data):
    """Extrae características técnicas de un DataFrame para predicción."""
    logger = logging.getLogger()
    if data.empty or len(data) < 2:
        logger.warning("⚠️ DataFrame vacío o insuficiente en extract_features.")
        return None

    data = data.sort_values('timestamp')
    prices = data['close'].values
    volumes = data['volume'].values

    # Calcular MACD y Bollinger Bands con manejo de datos insuficientes
    macd_value = 0.0
    bb_position = 0.0
    if len(prices) >= 26:  # MACD requiere al menos 26 velas
        macd, macd_signal, _ = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
        macd_value = macd[-1] if len(macd) > 0 and not np.isnan(macd[-1]) else 0.0
    if len(prices) >= 20:  # Bollinger Bands requiere al menos 20 velas
        upper, middle, lower = talib.BBANDS(prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        bb_position = (prices[-1] - middle[-1]) / (upper[-1] - lower[-1]) if upper[-1] != lower[-1] and not np.isnan(middle[-1]) else 0.0

    features = [
        prices[-1],  # Último precio de cierre
        np.mean(prices),  # Media de precios
        prices[-1] - np.mean(prices),  # Diferencia respecto a la media
        np.std(prices),  # Desviación estándar
        (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 and prices[-2] != 0 else 0.0,  # Retorno inmediato
        talib.RSI(prices, timeperiod=5)[-1] if len(prices) >= 14 and not np.isnan(talib.RSI(prices, timeperiod=5)[-1]) else 0.0,  # RSI ajustado
        talib.EMA(prices, timeperiod=10)[-1] if len(prices) >= 10 and not np.isnan(talib.EMA(prices, timeperiod=10)[-1]) else 0.0,  # EMA corta
        np.mean(volumes),  # Media de volumen
        macd_value,  # Valor de MACD
        bb_position,  # Posición relativa en Bollinger Bands
    ]
    return np.array(features).reshape(1, -1)