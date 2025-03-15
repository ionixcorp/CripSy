import logging
from risk.risk_manager import get_trade_size

class Trader:
    def __init__(self, config, api):
        self.config = config
        self.api = api
        self.logger = logging.getLogger()

    def trade(self, consolidated_signal):
        direction = consolidated_signal.get("direction")
        confidence = consolidated_signal.get("confidence")
        self.logger.info(f"Ejecutando operación: Dirección={direction}, Confianza={confidence:.2f}")

        if direction not in ["call", "put"]:
            self.logger.info("Señal inválida. No se ejecuta operación.")
            return

        try:
            current_balance = self.api.get_balance()
            self.logger.info(f"Balance actual: {current_balance:.2f} USD")
            trade_amount = get_trade_size(current_balance, self.config.risk_percentage)
            duration = 60  # Duración de la operación en segundos
            # Se actualiza la llamada para la nueva API: buy_digital_option (en lugar de buy_digital_spot)
            self.api.buy_digital_option(self.config.data_order, trade_amount, direction, duration)
            self.logger.info(f"💰 Operación ejecutada: {direction.upper()} por {trade_amount:.2f} USD, duración {duration} segundos")
        except Exception as e:
            self.logger.error(f"❌ Error al ejecutar la operación: {e}")
