import logging
from enum import Enum

class LogLevel(Enum):
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    DEBUG = logging.DEBUG

_logger = None

def get_logger(name: str):
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
    return _logger

def log_info(logger, message):
    logger.info(message)

def log_warning(logger, message, error_code=None):
    if error_code:
        logger.warning(f"{error_code}: {message}")
    else:
        logger.warning(message)

def log_error(logger, message, error_code=None):
    if error_code:
        logger.error(f"{error_code}: {message}")
    else:
        logger.error(message)
