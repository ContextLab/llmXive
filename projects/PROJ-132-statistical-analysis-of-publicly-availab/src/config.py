"""
Configuration module for the Bird Migration Climate Correlation project.
Contains constants, logging setup, and assumption targets.
"""
import logging
import os
from pathlib import Path
from typing import Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Global Constants
SEED = 42
GRID_RES = 0.5
PERMUTATIONS = 10000

# Assumption Targets (SC-001 to SC-004)
# These are concrete numeric values for success criteria measurement.
POWER_TARGET = 0.80
INSUFFICIENT_DATA_TARGET = 0.20
CONVERGENCE_TARGET = 0.90
CI_WIDTH_TARGET = 5.0

# Runtime Constraint (SC-005)
MAX_RUNTIME_HOURS = 6.0

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

def setup_logging(name: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.
    
    Args:
        name: Logger name (defaults to module name if None)
        log_file: Specific log file path (defaults to project logs dir if None)
        
    Returns:
        Configured logging.Logger instance
    """
    logger_name = name if name else __name__
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file) if log_file else (LOGS_DIR / "pipeline.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def verify_config_targets() -> bool:
    """
    Verify that all assumption targets are set to valid numeric values.
    
    Returns:
        True if all targets are valid, False otherwise.
    """
    targets = {
        "POWER_TARGET": POWER_TARGET,
        "INSUFFICIENT_DATA_TARGET": INSUFFICIENT_DATA_TARGET,
        "CONVERGENCE_TARGET": CONVERGENCE_TARGET,
        "CI_WIDTH_TARGET": CI_WIDTH_TARGET
    }
    
    for name, value in targets.items():
        if not isinstance(value, (int, float)):
            logging.error(f"Target {name} is not a numeric value: {value}")
            return False
        if value < 0 or value > 100:
            # Allow > 1 for CI width, but check others
            if name != "CI_WIDTH_TARGET" and (value < 0 or value > 1):
                logging.error(f"Target {name} value {value} is outside expected range [0, 1]")
                return False
                
    return True

# Initialize default logger
logger = setup_logging()

if __name__ == "__main__":
    # Test verification
    if verify_config_targets():
        logger.info("All configuration targets are valid.")
        logger.info(f"POWER_TARGET: {POWER_TARGET}")
        logger.info(f"INSUFFICIENT_DATA_TARGET: {INSUFFICIENT_DATA_TARGET}")
        logger.info(f"CONVERGENCE_TARGET: {CONVERGENCE_TARGET}")
        logger.info(f"CI_WIDTH_TARGET: {CI_WIDTH_TARGET}")
    else:
        logger.error("Configuration target validation failed.")