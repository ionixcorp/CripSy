def get_price_action_signal(data):
    """
    Genera una señal basada en análisis de Price Action.
    Se asume que 'data' es un DataFrame con columnas 'close', 'open', etc.
    """
    try:
        latest = data.iloc[-1]
        if latest['close'] > latest['open']:
            return "call", 0.7  # Señal 'call' con confianza 0.7
        else:
            return "put", 0.7   # Señal 'put' con confianza 0.7
    except Exception:
        return None, 0.0