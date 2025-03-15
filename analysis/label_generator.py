import pandas as pd
import logging

class LabelGenerator:
    def __init__(self, config):
        self.config = config
        self.data_file = self.config.csv_path
        self.logger = logging.getLogger()

    def generate_labels(self):
        try:
            data = pd.read_csv(self.data_file)
            if len(data) < 2:
                self.logger.warning("ℹ️ Insuficientes datos para generar etiquetas.")
                return False
            data['label'] = (data['close'].shift(-1) > data['close']).astype(int)
            data = data[:-1]
            data.to_csv(self.data_file, index=False)
            self.logger.info(f"✅ Etiquetas generadas en {self.data_file}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error al generar etiquetas: {e}")
            return False