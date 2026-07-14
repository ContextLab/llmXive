import logging
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logs."""
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    """Setup logging infrastructure."""
    global _logger_instance
    
    if _logger_instance:
        return _logger_instance

    _logger_instance = logging.getLogger("llmXive")
    _logger_instance.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    _logger_instance.addHandler(ch)

    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(JsonFormatter())
        _logger_instance.addHandler(fh)

    return _logger_instance

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def log_metric(name: str, value: float, step: Optional[int] = None):
    """Log a metric value."""
    logger.info(f"Metric {name}: {value}")

def log_pipeline_event(event: str):
    """Log a pipeline event."""
    logger.info(f"Pipeline Event: {event}")

def main():
    """Entry point for logging config."""
    setup_logging()
    logger.info("Logging configuration loaded.")

if __name__ == "__main__":
    main()
