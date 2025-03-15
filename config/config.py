import os
from datetime import time

class Config:
    def __init__(self):
        # Se utiliza 'username' en lugar de 'email' según la nueva documentación.
        self.username = os.getenv("IQ_USERNAME")
        self.password = os.getenv("IQ_PASSWORD")
        # Se actualiza la variable de entorno para el tipo de mercado a 'MARKET_TYPE'
        self.market_type = os.getenv("MARKET_TYPE", "otc")
        self.data_assets = os.getenv("IQ_DATA_ASSETS", "EURUSD-OTC")
        self.mode = os.getenv("IQ_MODE", "digital")  # 'digital' para OTC o 'forex' para el mercado tradicional
        self.data_path = "data/"
        if self.mode.lower() == "digital":
            self.csv_path = f"{self.data_path}{self.data_assets}_Digital.csv"
            self.model_path = f"models/{self.data_assets}_Digital.keras"
            # Horarios para el mercado digital (defínelos según información real)
            self.market_open = time(8, 0)    # Ej: abre a las 08:00
            self.market_close = time(17, 0)  # Ej: cierra a las 17:00
        else:
            self.csv_path = f"{self.data_path}{self.data_assets}_Forex.csv"
            self.model_path = f"models/{self.data_assets}_Forex.keras"
            # Horarios para el mercado Forex
            self.market_open = time(7, 0)
            self.market_close = time(16, 0)
            
        self.data_order = os.getenv("IQ_DATA_ORDER", f"{self.data_assets}-op")
        self.data_window_seconds = int(os.getenv("DATA_WINDOW_SECONDS", "61080"))
        self.threshold_call = 0.0005
        self.threshold_put = -0.0005
        self.risk_percentage = 0.05

if __name__ == "__main__":
    config = Config()
    print("Configuración:", vars(config))
