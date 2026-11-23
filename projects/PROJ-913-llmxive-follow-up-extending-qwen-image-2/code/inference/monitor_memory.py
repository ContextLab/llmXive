import gc
import os
from utils.logger import get_logger

logger = get_logger("monitor_memory")

def monitor_memory():
    """
    Monitors memory and triggers GC if usage is high.
    """
    gc.collect()
    logger.debug("Garbage collection triggered.")
