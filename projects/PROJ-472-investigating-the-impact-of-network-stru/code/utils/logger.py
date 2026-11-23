import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

def setup_logger(name: str, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    return logger

def get_logger(name: str):
    return setup_logger(name)

class ResearchError(Exception):
    pass

class DataLoadError(Exception):
    pass

class SimulationError(Exception):
    pass

class AnalysisError(Exception):
    pass

class ConfigError(Exception):
    pass

class StructuredErrorFilter(logging.Filter):
    def filter(self, record):
        # Filter logic if needed
        return True

def get_traceback_info(exc: Exception):
    return traceback.format_exc()

def log_exception(exc: Exception, logger: logging.Logger):
    logger.error(f"Exception: {exc}")
    logger.error(get_traceback_info(exc))

def log_pipeline_start():
    logging.info("Pipeline started")

def log_pipeline_end(status: str = "success"):
    logging.info(f"Pipeline ended with status: {status}")

def handle_exceptions(exc: Exception):
    log_exception(exc, get_logger(__name__))

def safe_execute(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_exceptions(e)
        return None
