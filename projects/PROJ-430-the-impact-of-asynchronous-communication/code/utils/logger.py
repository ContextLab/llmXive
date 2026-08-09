"""
Logging utility with JSON formatting for pipeline monitoring.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = setup_logger(name, log_file="logs/pipeline.log")
    return _logger

def log_event(event_type: str, data: Dict[str, Any]):
    logger = get_logger()
    logger.info(json.dumps({"event": event_type, "data": data}))

def log_pipeline_start():
    logger = get_logger()
    logger.info("Pipeline started.")

def log_pipeline_complete():
    logger = get_logger()
    logger.info("Pipeline completed.")

def log_pipeline_error(error_msg: str):
    logger = get_logger()
    logger.error(f"Pipeline error: {error_msg}")

def log_language_exclusion_rate(project_id: str, total_comments: int, excluded_count: int):
    """
    Log the exclusion rate for non-English text per project.
    
    Args:
        project_id: The unique identifier for the project.
        total_comments: Total number of comments processed.
        excluded_count: Number of comments excluded due to non-English language.
    """
    if total_comments == 0:
        exclusion_rate = 0.0
    else:
        exclusion_rate = excluded_count / total_comments

    log_data = {
        "project_id": project_id,
        "total_comments": total_comments,
        "excluded_count": excluded_count,
        "exclusion_rate": exclusion_rate
    }
    
    logger = get_logger()
    logger.info(json.dumps({
        "event": "language_exclusion_rate",
        "data": log_data
    }))