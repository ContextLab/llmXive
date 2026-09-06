import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from config import Config

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)

def get_logger(name: str, config: Config = None, log_to_file: bool = True) -> logging.Logger:
    """
    Creates and configures a logger.
    
    Args:
        name: Name of the logger.
        config: Config object for log paths.
        log_to_file: If True, logs to data/logs/ as well as stdout.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    if log_to_file and config:
        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = JsonFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_event(logger: logging.Logger, event_type: str, data: dict):
    """
    Helper to log structured events.
    
    Args:
        logger: The logger instance.
        event_type: Type of event (e.g., 'phase_transition', 'metric_update').
        data: Dictionary of event data.
    """
    message = f"[{event_type}] {json.dumps(data)}"
    logger.info(message)
