from strategies.price_action import get_price_action_signal
from strategies.momentum import get_momentum_signal
from strategies.news_impact import get_news_signal

def get_all_signals(data, news=None):
    """
    Obtiene todas las señales combinadas a partir de las estrategias implementadas.
    """
    signals = []
    pa_signal, pa_conf = get_price_action_signal(data)
    signals.append({'strategy': 'price_action', 'signal': pa_signal, 'confidence': pa_conf})
    
    m_signal, m_conf = get_momentum_signal(data)
    signals.append({'strategy': 'momentum', 'signal': m_signal, 'confidence': m_conf})
    
    n_signal, n_conf = get_news_signal(news)
    signals.append({'strategy': 'news_impact', 'signal': n_signal, 'confidence': n_conf})
    
    # Se puede agregar más estrategias, por ejemplo, candle_patterns, si se desea.
    
    return signals