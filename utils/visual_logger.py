# utils/visual_logger.py
import sys
import time

class VisualLogger:
    def __init__(self, refresh_interval=1):
        self.last_update = 0
        self.refresh_interval = refresh_interval  # Intervalo mínimo para refrescar (en segundos)

    def update(self, message):
        """
        Actualiza en línea el mensaje en la consola.
        Solo se refresca si ha transcurrido al menos el refresh_interval.
        """
        current_time = time.time()
        if current_time - self.last_update >= self.refresh_interval:
            sys.stdout.write("\r" + message)
            sys.stdout.flush()
            self.last_update = current_time

    def clear(self):
        """Limpia la línea actual."""
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()