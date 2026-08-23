import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Singleton logger instance
_logger_instance: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create the project logger.
    
    Args:
        name: Name for the logger.
        
    Returns:
        Configured logger instance.
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = setup_logging(name)
        
    return _logger_instance


def setup_logging(name: str = "llmXive", level: Optional[int] = None) -> logging.Logger:
    """
    Configure the root logger for the project.
    
    Args:
        name: Name for the logger.
        level: Logging level (defaults to INFO).
        
    Returns:
        Configured logger instance.
    """
    global _logger_instance
    
    if level is None:
        level = logging.INFO
        
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger
        
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    _logger_instance = logger
    
    return logger


def configure_lineage(log_file: Optional[str] = None) -> None:
    """
    Configure file logging for data lineage tracking.
    
    Args:
        log_file: Path to the log file. Defaults to a timestamped file in logs/.
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = setup_logging()
        
    if not log_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = str(log_dir / f"lineage_{timestamp}.log")
        
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    
    _logger_instance.addHandler(file_handler)
    _logger_instance.debug(f"Lineage logging configured to: {log_file}")


class LineageAdapter(logging.LoggerAdapter):
    """
    Logger adapter to inject lineage information into log messages.
    """
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        if "lineage" in extra:
            msg = f"[Lineage: {extra['lineage']}] {msg}"
        return msg, kwargs