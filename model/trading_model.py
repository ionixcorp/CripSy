import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import os
import time
from utils.logger import setup_logger

class TradingModel:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.sequence_length = 10
        self.epochs = getattr(config, 'training_epochs', 10)  # Valor por defecto: 10
        self.logger = setup_logger()

    def build_model(self, input_shape):
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        self.model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])
        self.logger.info("🛠️ Modelo construido con éxito")

    def extract_features(self, df):
        # Ejemplo: Calcular MACD y otros indicadores
        df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema12'] - df['ema26']
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df = df.dropna()
        return df[['open', 'close', 'min', 'max', 'macd', 'signal']].values

    def prepare_data(self, df):
        if len(df) < self.sequence_length + 26:  # 26 para MACD + 10 para secuencia
            self.logger.error(f"❌ No hay suficientes datos para preparar el modelo: {len(df)} velas")
            return None, None
        features = self.extract_features(df)
        X, y = [], []
        for i in range(len(features) - self.sequence_length):
            X.append(features[i:(i + self.sequence_length)])
            # Ejemplo simple: 1 si el precio sube, 0 si baja
            y.append(1 if features[i + self.sequence_length, 1] > features[i + self.sequence_length - 1, 1] else 0)
        return np.array(X), np.array(y)

    def train(self, df):
        X, y = self.prepare_data(df)
        if X is None or y is None:
            return False
        if self.model is None:
            self.build_model((self.sequence_length, X.shape[2]))
        self.model.fit(X, y, epochs=self.epochs, batch_size=32, validation_split=0.1, verbose=1)
        self.model.save(self.config.model_path)
        self.logger.info(f"💾 Modelo entrenado y guardado en {self.config.model_path}")
        return True

    def load_model(self):
        if os.path.exists(self.config.model_path):
            self.model = tf.keras.models.load_model(self.config.model_path)
            self.logger.info(f"📥 Modelo cargado desde {self.config.model_path}")
            return True
        self.logger.warning("⚠️ No se encontró un modelo preentrenado")
        return False

    def predict(self, df):
        if self.model is None or not self.load_model():
            self.logger.error("❌ No se pudo cargar el modelo para predicción")
            return None
        features = self.extract_features(df)
        X = []
        for i in range(len(features) - self.sequence_length + 1):
            X.append(features[i:(i + self.sequence_length)])
        X = np.array(X)
        prediction = self.model.predict(X)[-1][0]
        decision = 'call' if prediction > 0.5 else 'put'
        confidence = abs(prediction - 0.5) * 2
        return {'decision': decision, 'confidence': confidence}

    def retrain_periodically(self, data_collector):
        while True:
            time.sleep(3600)  # Esperar 1 hora
            df_new = data_collector.get_latest_candles()  # Obtener velas de la última hora
            if len(df_new) > 0:
                df_historical = pd.read_csv(self.config.csv_path)
                df_combined = pd.concat([df_historical, df_new]).drop_duplicates(subset=['timestamp'], keep='last')
                if self.train(df_combined):
                    self.logger.info("✅ Modelo reentrenado con nuevos datos")