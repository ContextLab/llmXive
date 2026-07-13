import logging
import sys
from .exceptions import DataInsufficientError, PowerWarning, SHAPError

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup a logger with standard formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def handle_data_insufficient(error: DataInsufficientError) -> None:
    """Handle DataInsufficientError by logging and re-raising."""
    logger = logging.getLogger(__name__)
    logger.critical(f"Data insufficient: {error}")
    raise error

def handle_power_warning(warning: PowerWarning) -> None:
    """Handle PowerWarning by logging."""
    logger = logging.getLogger(__name__)
    logger.warning(f"Power warning: {warning}")

def handle_shap_error(error: SHAPError) -> None:
    """Handle SHAPError by logging and re-raising."""
    logger = logging.getLogger(__name__)
    logger.error(f"SHAP computation error: {error}")
    raise error
