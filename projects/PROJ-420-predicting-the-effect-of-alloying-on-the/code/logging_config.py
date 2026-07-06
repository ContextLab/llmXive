import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
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

def setup_logging(log_level: int = logging.INFO, log_file: Optional[Path] = None) -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
        
    return root_logger

def get_logger(name: str) -> logging.Logger:
    # Ensure logging is set up if not already
    if not logging.getLogger().handlers:
        setup_logging()
    return logging.getLogger(name)

def log_with_extra(logger: logging.Logger, level: int, msg: str, **extra: Any):
    logger.log(level, msg, extra=extra)

def main():
    logger = get_logger(__name__)
    logger.info("Logging system initialized.")
    logger.warning("This is a test warning.")
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("Division by zero occurred.")

if __name__ == "__main__":
    main()