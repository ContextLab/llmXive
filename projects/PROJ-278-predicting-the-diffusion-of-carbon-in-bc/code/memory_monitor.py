import psutil
import os
import atexit
import logging
from typing import Optional

_process = psutil.Process(os.getpid())
_peak_memory_mb = 0.0
_monitoring = False

def update_peak_memory():
    global _peak_memory_mb
    current = _process.memory_info().rss / 1024 / 1024
    if current > _peak_memory_mb:
        _peak_memory_mb = current

def get_peak_memory_mb() -> float:
    update_peak_memory()
    return _peak_memory_mb

def reset_peak_memory():
    global _peak_memory_mb
    _peak_memory_mb = 0.0

def log_peak_memory():
    logging.info(f"Peak memory usage: {get_peak_memory_mb():.2f} MB")

def monitor_memory_interval():
    pass # Placeholder for interval monitoring if needed

@atexit.register
def final_log():
    log_peak_memory()
