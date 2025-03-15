import logging

class StrategyAnalyzer:
    def __init__(self, ml_model):
        self.logger = logging.getLogger()
        self.ml_model = ml_model

    def consolidate_signals(self, signals, data_context):
        if not signals:
            self.logger.warning("No se recibieron señales para consolidar.")
            return {"direction": "neutral", "confidence": 0, "strategy": None}
        
        direction_confidence = {}
        strategy_for_direction = {}
        for s in signals:
            direction = s.get("signal")
            conf = s.get("confidence", 0)
            if direction in direction_confidence:
                direction_confidence[direction] += conf
            else:
                direction_confidence[direction] = conf
                strategy_for_direction[direction] = s.get("strategy", "unknown")
        
        chosen_direction = max(direction_confidence, key=direction_confidence.get)
        total_confidence = direction_confidence[chosen_direction]
        dominant_strategy = strategy_for_direction.get(chosen_direction, "unknown")
        self.logger.info(f"Consolidación: dirección {chosen_direction}, confianza {total_confidence:.2f}, estrategia {dominant_strategy}")
        return {"direction": chosen_direction, "confidence": total_confidence, "strategy": dominant_strategy}