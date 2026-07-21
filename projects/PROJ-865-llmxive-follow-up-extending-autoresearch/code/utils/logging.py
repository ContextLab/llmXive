"""
Structured logging utilities for the pipeline.
"""
import logging
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
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

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO):
    """Configure root logger with console and optional file handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if path provided
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def log_resource_usage():
    """Log current CPU and memory usage if psutil is available."""
    try:
        import psutil
        process = psutil.Process()
        cpu_percent = process.cpu_percent()
        mem_info = process.memory_info()
        logger = get_logger(__name__)
        logger.info(f"Resource Usage - CPU: {cpu_percent}%, RAM: {mem_info.rss / 1024 / 1024:.2f} MB")
    except ImportError:
        pass

def log_stage_start(stage_name: str):
    logger = get_logger(__name__)
    log_resource_usage()
    logger.info(f"--- START STAGE: {stage_name} ---")

def log_stage_end(stage_name: str):
    logger = get_logger(__name__)
    log_resource_usage()
    logger.info(f"--- END STAGE: {stage_name} ---")

class StageFilter(logging.Filter):
    def __init__(self, stage_name: Optional[str] = None):
        self.stage_name = stage_name
    
    def filter(self, record: logging.LogRecord) -> bool:
        if self.stage_name:
            # Simple filter: only log if message contains stage name or is a stage marker
            if "START STAGE" in record.getMessage() or "END STAGE" in record.getMessage():
                return True
            if self.stage_name in record.getMessage():
                return True
            return False
        return True

def get_pipeline_logger(name: str, stage_filter: Optional[StageFilter] = None):
    logger = get_logger(name)
    if stage_filter:
        logger.addFilter(stage_filter)
    return logger
