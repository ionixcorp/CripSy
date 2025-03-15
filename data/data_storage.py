import pandas as pd
import os
from utils.logger import setup_logger

class DataStorage:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.logger = setup_logger()

    def save_candles(self, candles, append=True):
        try:
            df = pd.DataFrame(candles)
            if append and self.has_data():
                # Cargar datos existentes
                existing_df = self.load_candles()
                # Combinar y eliminar duplicados basados en timestamp ('from')
                combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['from'], keep='last')
                combined_df.to_csv(self.csv_path, index=False)
            else:
                df.to_csv(self.csv_path, index=False)
            self.logger.info(f"Guardadas {len(candles)} velas en {self.csv_path}")
        except Exception as e:
            self.logger.error(f"Error al guardar velas: {e}")

    def load_candles(self):
        try:
            if self.has_data():
                df = pd.read_csv(self.csv_path)
                return df.to_dict('records')
            return []
        except Exception as e:
            self.logger.error(f"Error al cargar velas: {e}")
            return []

    def has_data(self):
        exists = os.path.exists(self.csv_path)
        size = os.path.getsize(self.csv_path) if exists else 0
        self.logger.debug(f"Verificando datos - Archivo: {self.csv_path}, Existe: {exists}, Tamaño: {size} bytes")
        return exists and size > 0