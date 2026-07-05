import logging
import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

class ProvenanceAdapter:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.provenance_log: list[Dict[str, Any]] = []

    def log(self, event: str, details: Dict[str, Any]):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "details": details,
        }
        self.provenance_log.append(entry)
        self._flush()

    def _flush(self):
        with open(self.output_path, "w") as f:
            json.dump(self.provenance_log, f, indent=2)

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "llmXive"):
    return logging.getLogger(name)

def log_provenance(logger: logging.Logger, event: str, details: Dict[str, Any]):
    logger.info(f"PROVENANCE: {event}", extra={"details": details})

def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any]):
    logger.error(f"ERROR: {str(error)}", extra={"context": context}, exc_info=True)
