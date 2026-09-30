import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

# Singleton logger instance
_logger_instance: Optional[logging.Logger] = None
_logging_initialized = False

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_root_logger(name: str = "llmXive", log_file: Optional[str] = None) -> logging.Logger:
    global _logging_initialized, _logger_instance

    if _logging_initialized:
        return _logger_instance

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = JsonFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _logger_instance = logger
    _logging_initialized = True
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    if not _logging_initialized:
        return setup_root_logger(name)
    return logging.getLogger(name)

def log_event(logger: logging.Logger, event: str, data: Dict[str, Any], level: str = "INFO") -> None:
    msg = f"{event}: {json.dumps(data)}"
    if level == "DEBUG":
        logger.debug(msg)
    elif level == "WARNING":
        logger.warning(msg)
    elif level == "ERROR":
        logger.error(msg)
    else:
        logger.info(msg)
