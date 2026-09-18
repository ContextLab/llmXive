import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(JSONFormatter())
    logger.addHandler(ch)

    # File handler
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(JSONFormatter())
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def log_event(logger: logging.Logger, event: str, data: Dict[str, Any]):
    logger.info(json.dumps({"event": event, "data": data}))

def log_sensitivity_results(logger: logging.Logger, results: Dict):
    log_event(logger, "sensitivity_analysis", results)

def main():
    logger = setup_logger("test_logger", "logs/test.log")
    logger.info("Test log message")

if __name__ == "__main__":
    main()
