import time
import threading
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from utils.logger import setup_logger
from utils.data_utils import clean_data

logger = setup_logger()

class DataCollector:
    def __init__(self, config):
        self.config = config
        self.logger = logger
        self.buffer = []
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 3 * 3600  # Cada 3 horas
        self.running = False
        self.thread = None
        self.api = self.connect_api()
    
    def connect_api(self):
        try:
            api = IQ_Option(self.config.email, self.config.password)
            api.connect()
            if api.check_connect():
                self.logger.info(f"📡 Conectado a IQ Option en modo {self.config.mode}")
                api.change_balance("PRACTICE")
                return api
            else:
                self.logger.error("❌ Error al conectar a IQ Option")
                raise ConnectionError("No se pudo conectar a IQ Option")
        except Exception as e:
            self.logger.error(f"❌ Error al conectar a la API: {e}")
            raise

    def fetch_historical_candles(self, count, max_retries=3):
        candles = []
        block_size = 1000
        end_time = int(time.time()) - 60
        remaining = count
        target_time = end_time - self.config.data_window_seconds

        while remaining > 0:
            fetch_count = min(block_size, remaining)
            for attempt in range(max_retries):
                candles_block = self.api.get_candles(self.config.data_assets, 60, fetch_count, end_time)
                if candles_block and len(candles_block) > 0:
                    candles.extend(candles_block)
                    self.logger.info(f"📊 Recolectadas {len(candles_block)} velas. Total: {len(candles)}/{count}")
                    if candles and candles[-1]['from'] <= target_time:
                        self.logger.info("🕒 Rango temporal cubierto. Deteniendo recolección histórica.")
                        remaining = 0
                        break
                    break
                else:
                    self.logger.warning(f"⚠️ Intento {attempt + 1}/{max_retries} fallido para {fetch_count} velas. Reconectando...")
            remaining -= fetch_count
            if candles:
                end_time = candles[-1]['from']
        return candles

    def collect_data(self, new_data):
        self.buffer.append(new_data)
        if time.time() - self.last_cleanup_time >= self.cleanup_interval:
            self.cleanup_data()

    def cleanup_data(self):
        if not self.buffer:
            self.logger.info("🧹 No hay datos para limpiar.")
            return
        df = pd.DataFrame(self.buffer)
        df.to_csv(self.config.csv_path, index=False)
        self.logger.info(f"💾 Guardadas {len(df)} velas en {self.config.csv_path}")
        self.buffer = []
        self.last_cleanup_time = time.time()

    def _realtime_loop(self):
        self.api.start_candles_stream(self.config.data_assets, 60, 20)
        while self.running:
            candles = self.api.get_realtime_candles(self.config.data_assets, 60)
            if candles:
                latest_timestamp = max(candles.keys())
                latest_candle = candles[latest_timestamp]
                self.logger.info(f"🕯️ Nueva vela: {latest_candle}")
                self.collect_data(latest_candle)
            time.sleep(1)

    def start_realtime(self):
        self.running = True
        self.thread = threading.Thread(target=self._realtime_loop)
        self.thread.start()
        self.logger.info("Recolección de datos en tiempo real iniciada.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()