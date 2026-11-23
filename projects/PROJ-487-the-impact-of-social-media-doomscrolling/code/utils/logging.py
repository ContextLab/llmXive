import logging
import os
import sys
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from config import Configuration

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    json_format: bool = True
) -> None:
    """
    Configure the root logger with file and console handlers.
    
    Args:
        log_file: Path to the log file. If None, uses a default location.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        json_format: Whether to use JSON formatting for log messages.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Determine log file path
    if log_file is None:
        project_root = Path(__file__).parent.parent.parent
        log_file = project_root / "logs" / "app.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter() if json_format else logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(JSONFormatter() if json_format else logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__).
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)

def configure_root_logger(config: Optional[Configuration] = None) -> None:
    """
    Configure the root logger based on configuration settings.
    
    Args:
        config: Configuration object (optional).
    """
    if config is None:
        config = Configuration()
    
    setup_logging(
        log_file=config.log_file,
        level=config.log_level,
        json_format=config.json_log_format
    )

def main():
    """Main entry point for logging configuration."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging configured successfully")

if __name__ == "__main__":
    main()