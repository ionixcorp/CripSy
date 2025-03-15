import time
from utils.logger import setup_logger

class TradeExecutor:
    def __init__(self, config):
        self.api = config.api
        self.asset = config.data_order  # Usar EURUSD-op para órdenes
        self.mode = config.mode
        self.logger = setup_logger()

    def execute_trade(self, direction, amount):
        expiration = 1  # 1 minuto
        try:
            check, trade_id = self.api.buy(amount, self.asset, direction, expiration)
            check_method = self.api.check_win_v2

            if check:
                self.logger.info(f"Operación ejecutada: {direction} por {amount} en {self.asset} modo {self.mode}, Trade ID: {trade_id}")
                while True:
                    result = check_method(trade_id)
                    if result is not None:
                        if isinstance(result, dict):
                            profit = result.get("profit", 0)
                        elif isinstance(result, (tuple, list)) and len(result) > 0:
                            profit = result[0] if isinstance(result[0], (int, float)) else 0
                        else:
                            profit = 0
                        self.logger.info(f"Resultado: {profit if profit > 0 else 'Pérdida'}")
                        break
                    time.sleep(0.5)
            else:
                self.logger.error(f"Error al ejecutar la operación, check: {check}")
        except Exception as e:
            self.logger.error(f"Error en ejecución: {e}")

    def pause(self, seconds):
        time.sleep(seconds)