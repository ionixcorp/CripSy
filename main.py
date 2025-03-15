import os
import time
import signal
import sys
import pandas as pd
import random
from datetime import datetime, timedelta
from config.config import Config
from utils.logger import setup_logger
from utils.visual_logger import VisualLogger
from data.data_collector import DataCollector
from analysis.label_generator import LabelGenerator
from analysis.ml_model import MLModel
from analysis.strategy_analyzer import StrategyAnalyzer
from trading.trader import Trader
from strategies.strategy_signals import get_all_signals

logger = setup_logger()
visual_logger = VisualLogger(refresh_interval=1)

# Función para imprimir la configuración actual para depuración
def print_config(config):
    logger.info("=== Configuración utilizada ===")
    logger.info(f"IQ_EMAIL: {config.email}")
    logger.info(f"IQ_PASSWORD: {config.password}")
    logger.info(f"IQ_MARKET_TYPE: {os.getenv('IQ_MARKET_TYPE')}")
    logger.info(f"IQ_DATA_ASSETS: {config.data_assets}")
    logger.info(f"IQ_DATA_ORDER: {config.data_order}")
    logger.info(f"IQ_MODE: {config.mode}")
    logger.info(f"CSV Path: {config.csv_path}")
    logger.info(f"Model Path: {config.model_path}")
    logger.info(f"DATA_WINDOW_SECONDS: {config.data_window_seconds}")
    logger.info("=============================")

# Función para verificar la disponibilidad del activo a operar.
# Se verifica si el activo se encuentra abierto utilizando la función adecuada
# según el modo de operación: digital, otc o tradicional.
def verify_asset_availability(api, asset, mode):
    try:
        # Para modo digital se utilizan velas digitales
        if mode.lower() == "digital":
            candles = api.get_digital_candles(asset, 60, 1)
        # Para mercados OTC se utiliza la función get_otc_candles
        elif mode.lower() == "otc":
            candles = api.get_otc_candles(asset, 60, 1)
        # Para otros modos (como forex) se asume el uso de get_candles
        else:
            candles = api.get_candles(asset, 60, 1)
            
        if candles:
            logger.info(f"Se recibieron velas para el activo {asset}.")
            return True
        else:
            logger.error(f"No se recibieron velas para el activo {asset}.")
            return False
    except Exception as e:
        logger.error(f"Error al obtener velas para {asset}: {e}")
        return False

# Función de verificación horaria (como antes)
def should_stop_operating(config, safety_margin_minutes=10):
    now = datetime.now().time()
    market_close = config.market_close
    now_dt = datetime.combine(datetime.today(), now)
    close_dt = datetime.combine(datetime.today(), market_close)
    if close_dt - now_dt <= timedelta(minutes=safety_margin_minutes):
        return True
    return False

def signal_handler(sig, frame):
    logger.info("🛑 Interrupción recibida, deteniendo el bot de forma controlada...")
    collector.stop()
    logger.info("✅ Bot detenido exitosamente")
    global running
    running = False

if __name__ == "__main__":
    config = Config()
    print_config(config)  # Imprime la configuración en los logs

    try:
        collector = DataCollector(config)
    except Exception as e:
        logger.error(f"❌ Error al inicializar DataCollector: {e}")
        sys.exit(1)
        
    signal.signal(signal.SIGINT, signal_handler)

    # Verificar la conexión a la API y la disponibilidad del activo
    if not verify_asset_availability(collector.api, config.data_assets, config.mode):
        logger.error("El activo no se encuentra disponible (cerrado o inaccesible). Deteniendo el bot.")
        sys.exit(1)

    # Verificar si el mercado se encuentra en horario operativo (basado en configuración)
    if should_stop_operating(config, safety_margin_minutes=10):
        logger.error("El mercado está a punto de cerrar. Deteniendo el bot. Revise la configuración del activo a operar.")
        sys.exit(1)
    
    # Cargar datos históricos
    if os.path.exists(config.csv_path):
        historical_data = pd.read_csv(config.csv_path)
        if 'timestamp' not in historical_data.columns and 'from' in historical_data.columns:
            historical_data.rename(columns={'from': 'timestamp'}, inplace=True)
        logger.info(f"📂 Datos históricos cargados desde {config.csv_path}: {len(historical_data)} registros")
    else:
        historical_data = pd.DataFrame()
    
    if historical_data.empty or (historical_data['timestamp'].max() - historical_data['timestamp'].min() < config.data_window_seconds):
        logger.info("📅 Datos históricos insuficientes o desactualizados. Recolectando nuevos datos...")
        candles = collector.fetch_historical_candles(15000)
        historical_data = pd.DataFrame(candles)
        if 'timestamp' not in historical_data.columns and 'from' in historical_data.columns:
            historical_data.rename(columns={'from': 'timestamp'}, inplace=True)
        historical_data.to_csv(config.csv_path, index=False)
        logger.info(f"💾 Guardados {len(historical_data)} registros en {config.csv_path}")
    
    label_generator = LabelGenerator(config)
    label_generator.generate_labels()
    
    ml_model = MLModel(config)
    if os.path.exists(config.model_path):
        model_mtime = os.path.getmtime(config.model_path)
        if time.time() - model_mtime < 3 * 3600:
            logger.info("🔄 Modelo existente es reciente; se utilizará sin reentrenamiento.")
        else:
            logger.info("⏳ Modelo existente es antiguo; se procederá a reentrenar.")
            ml_model.train(historical_data)
    else:
        ml_model.train(historical_data)
    
    collector.start_realtime()
    
    trader = Trader(config, collector.api)
    strategy_analyzer = StrategyAnalyzer(ml_model)
    
    # Variables para el ciclo de análisis
    min_analysis_period = 300        # 5 minutos de análisis inicial sin operar
    extra_confidence_factor = 0.001    # Incremento de confianza por segundo extra
    MIN_CONFIDENCE_THRESHOLD = 1.0     # Umbral mínimo para emitir una orden
    cycle_start = time.time()          # Marca de inicio del ciclo
    running = True

    logger.info("Iniciando ciclo de análisis y operaciones...")
    while running:
        if should_stop_operating(config, safety_margin_minutes=10):
            logger.error("El mercado está a punto de cerrar. Deteniendo el bot. Revise la configuración del activo a operar.")
            sys.exit(1)
        
        if not verify_asset_availability(collector.api, config.data_assets, config.mode):
            logger.error("El activo se encuentra cerrado o inaccesible. Deteniendo el bot.")
            sys.exit(1)
        
        realtime_data = pd.read_csv(config.csv_path)
        if 'timestamp' not in realtime_data.columns and 'from' in realtime_data.columns:
            realtime_data.rename(columns={'from': 'timestamp'}, inplace=True)
        if len(realtime_data) < ml_model.sequence_length:
            time.sleep(1)
            continue

        current_time = time.time()
        elapsed = current_time - cycle_start

        # Fase de calibración: durante los primeros 5 minutos se acumulan datos sin operar.
        if elapsed < min_analysis_period:
            visual_logger.update(f"🔍 Reconociendo mercado. Tiempo transcurrido: {int(elapsed)} seg")
            time.sleep(1)
            continue
        else:
            visual_logger.clear()
        
        # Fase dinámica: evaluar señales y acumular confianza.
        signals = get_all_signals(realtime_data, news=None)
        logger.info(f"Señales generadas: {signals}")
        
        consolidated_signal = strategy_analyzer.consolidate_signals(signals, realtime_data)
        base_confidence = consolidated_signal.get("confidence", 0)
        direction = consolidated_signal.get("direction")
        logger.info(f"Señal consolidada preliminar: {direction} con confianza {base_confidence:.2f}")
        
        ml_validation = ml_model.predict(realtime_data)
        logger.info(f"Validación ML: {ml_validation}")
        if ml_validation == direction:
            base_confidence += 0.1
            logger.info("La validación ML coincide. Refuerzo aplicado.")
        
        extra_time = elapsed - min_analysis_period
        effective_confidence = base_confidence + extra_time * extra_confidence_factor
        
        visual_logger.update(f"⏱️ Extra: {int(extra_time)} seg | Confianza: {effective_confidence:.2f} (umbral: {MIN_CONFIDENCE_THRESHOLD})")
        
        if direction in ["call", "put"] and effective_confidence >= MIN_CONFIDENCE_THRESHOLD:
            visual_logger.clear()
            logger.info("Umbral alcanzado. Ejecutando operación...")
            trader.trade(consolidated_signal)
            logger.info("Operación ejecutada. Esperando a que finalice...")
            trade_duration = 60  # 60 segundos
            time.sleep(trade_duration + 5)
            cycle_start = time.time()
        else:
            time.sleep(1)
