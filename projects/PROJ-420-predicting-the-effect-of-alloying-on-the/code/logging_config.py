import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "data/logs/pipeline.log"

def setup_logging():
    """Configure logging for the project."""
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    
    # Clear existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def log_with_extra(msg: str, extra: Dict[str, Any]):
    """Log a message with extra context."""
    logger = get_logger(__name__)
    logger.info(msg, extra=extra)

def main():
    """Test logging setup."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging initialized.")

if __name__ == "__main__":
    main()
