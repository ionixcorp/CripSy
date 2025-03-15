import talib
import numpy as np
from utils.logger import setup_logger

class TradingStrategies:
    def __init__(self):
        self.logger = setup_logger()

    def price_action(self, data):
        """
        Detecta soporte y resistencia a partir de las últimas 10 velas.
        Retorna 'call' si el precio actual es menor o igual al soporte,
        'put' si es mayor o igual a la resistencia, o None en caso contrario.
        """
        close_prices = np.array(data['close'])
        support = np.min(close_prices[-10:])
        resistance = np.max(close_prices[-10:])
        self.logger.info(f"Price Action - Soporte: {support}, Resistencia: {resistance}")
        if close_prices[-1] <= support:
            return "call", 0.8
        elif close_prices[-1] >= resistance:
            return "put", 0.8
        return None, 0.0

    def momentum(self, data):
        """
        Evalúa la tendencia mediante el RSI.
        Retorna 'call' si el RSI es menor a 30 y 'put' si es mayor a 70.
        """
        rsi = talib.RSI(np.array(data['close']), timeperiod=14)
        self.logger.info(f"Momentum - RSI: {rsi[-1]}")
        if rsi[-1] > 70:
            return "put", 0.7
        elif rsi[-1] < 30:
            return "call", 0.7
        return None, 0.0

    def news_impact(self, recent_news):
        """
        Evalúa el impacto de noticias relevantes.
        Si se detecta 'high impact', retorna 'call' para noticias positivas o 'put' para negativas.
        """
        self.logger.info("Evaluando impacto de noticias")
        if 'high impact' in recent_news:
            return ("call", 0.6) if "positive" in recent_news else ("put", 0.6)
        return None, 0.0

    # Se pueden agregar otros métodos para estrategias adicionales.