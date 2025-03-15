import numpy as np
import pandas as pd
import logging
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Input, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import backend as K
from sklearn.preprocessing import MinMaxScaler
import talib
import time
from joblib import dump, load

def custom_binary_crossentropy(y_true, y_pred):
    epsilon = 1e-7
    y_pred = tf.clip_by_value(y_pred, epsilon, 1.0 - epsilon)
    return K.binary_crossentropy(y_true, y_pred)

class MLModel:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger()
        self.model = None
        self.scaler = MinMaxScaler()
        self.sequence_length = 10
        self.input_features = 10
        self.last_train_time = 0
        self.retrain_interval = 3 * 3600

    def build_model(self):
        self.model = Sequential([
            Input(shape=(self.sequence_length, self.input_features)),
            LSTM(100, return_sequences=True),
            LSTM(100),
            Dense(50, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        optimizer = Adam(learning_rate=0.0001, clipnorm=1.0)
        self.model.compile(optimizer=optimizer, loss=custom_binary_crossentropy, metrics=['accuracy'])
        self.logger.info("🧠 Modelo LSTM creado con éxito.")

    def extract_features_df(self, data):
        data = data.sort_values('timestamp').reset_index(drop=True)
        prices = data['close'].values
        volumes = data['volume'].values

        if len(prices) >= 26:
            macd, macd_signal, _ = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
        else:
            macd = np.zeros_like(prices)
        if len(prices) >= 20:
            upper, middle, lower = talib.BBANDS(prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            bb_position = (prices - middle) / (upper - lower + 1e-6)
        else:
            bb_position = np.zeros_like(prices)
        if len(prices) >= 14:
            rsi = talib.RSI(prices, timeperiod=5)
        else:
            rsi = np.zeros_like(prices)
        if len(prices) >= 10:
            ema10 = talib.EMA(prices, timeperiod=10)
        else:
            ema10 = np.zeros_like(prices)

        roll_mean = pd.Series(prices).rolling(window=10, min_periods=1).mean().values
        roll_std = pd.Series(prices).rolling(window=10, min_periods=1).std().fillna(0).values
        ret = np.concatenate(([0], (prices[1:] - prices[:-1]) / (prices[:-1] + 1e-6)))
        features = np.column_stack([
            prices,
            roll_mean,
            prices - roll_mean,
            roll_std,
            ret,
            rsi,
            ema10,
            pd.Series(volumes).rolling(window=10, min_periods=1).mean().values,
            macd,
            bb_position
        ])
        features = np.nan_to_num(features, nan=0.0)
        return features

    def prepare_training_data(self, data):
        data = data.sort_values('timestamp').reset_index(drop=True)
        if 'label' not in data.columns:
            self.logger.warning("Columna 'label' no encontrada. Generándola automáticamente.")
            data['label'] = (data['close'].shift(-1) > data['close']).astype(int)
            data = data[:-1]
        feature_matrix = self.extract_features_df(data)
        X, y = [], []
        for i in range(len(feature_matrix) - self.sequence_length):
            X.append(feature_matrix[i:i+self.sequence_length])
            y.append(data['label'].iloc[i+self.sequence_length-1])
        if not X:
            self.logger.error("❌ No se pudieron extraer características para entrenamiento")
            return None, None
        X = np.array(X)
        y = np.array(y)
        num_samples, seq_len, num_features = X.shape
        X_2d = X.reshape(-1, num_features)
        X_scaled = self.scaler.fit_transform(X_2d)
        X = X_scaled.reshape(num_samples, seq_len, num_features)
        return X, y

    def train(self, data):
        if data.empty or len(data) < self.sequence_length + 1:
            self.logger.error("❌ Datos insuficientes para entrenar el modelo")
            return
        if time.time() - self.last_train_time < self.retrain_interval and self.model is not None:
            self.logger.info("No es tiempo de reentrenar aún.")
            return
        X, y = self.prepare_training_data(data)
        if X is None or y is None:
            return
        self.build_model()
        self.model.fit(X, y, epochs=50, batch_size=32, validation_split=0.2, verbose=1)
        self.model.save(self.config.model_path)
        dump(self.scaler, f"{self.config.data_assets}_scaler.pkl")
        self.last_train_time = time.time()
        self.logger.info(f"💾 Modelo entrenado y guardado en {self.config.model_path}")

    def predict(self, data):
        if self.model is None:
            try:
                self.model = load_model(self.config.model_path, custom_objects={'custom_binary_crossentropy': custom_binary_crossentropy})
                self.logger.info(f"📦 Modelo cargado desde {self.config.model_path}")
            except Exception as e:
                self.logger.error(f"❌ Error al cargar el modelo: {e}")
                return None
        if not hasattr(self.scaler, 'min_'):
            try:
                self.scaler = load(f"{self.config.data_assets}_scaler.pkl")
            except Exception as e:
                self.logger.error(f"❌ Error al cargar el scaler: {e}")
                return None
        data = data.sort_values('timestamp').reset_index(drop=True)
        feature_matrix = self.extract_features_df(data)
        if len(feature_matrix) < self.sequence_length:
            self.logger.error("❌ Datos insuficientes para predicción")
            return None
        X = feature_matrix[-self.sequence_length:]
        X = self.scaler.transform(X)
        X = X.reshape(1, self.sequence_length, self.input_features)
        prediction = self.model.predict(X)
        return "call" if prediction[0][0] > 0.5 else "put"