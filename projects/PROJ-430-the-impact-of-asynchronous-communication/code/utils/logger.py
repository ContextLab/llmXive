"""
Logging utility with JSON formatting for pipeline monitoring.
Implements Constitution Principle V (Hygiene) and VI (Modality Separation) support.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines for easy parsing and monitoring."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry)

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with JSON formatting for both console and file output.
    
    Args:
        name: Logger name
        log_file: Optional file path for log output
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if logger is re-configured
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

# Global logger instance
_logger: Optional[logging.Logger] = None
_logger_name: str = "llmXive"

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a global logger instance.
    
    Args:
        name: Logger name (default: "llmXive")
    
    Returns:
        Logger instance
    """
    global _logger, _logger_name
    if _logger is None:
        # Try to get config for log path, fallback to default
        try:
            from config import get_config
            config = get_config()
            log_path = config.get('log_path', 'data/logs/pipeline.log')
        except Exception:
            log_path = 'data/logs/pipeline.log'
        
        _logger_name = name
        _logger = setup_logger(name, log_file=log_path)
    return _logger

def log_event(event_type: str, data: Dict[str, Any]):
    """
    Log a structured event with arbitrary data payload.
    
    Args:
        event_type: Type of event (e.g., 'data_loaded', 'metric_calculated')
        data: Dictionary of event data
    """
    logger = get_logger()
    logger.info(json.dumps({"event": event_type, "data": data}), extra={'extra_data': {"event": event_type, "data": data}})

def log_pipeline_start():
    """Log the start of the pipeline execution."""
    logger = get_logger()
    logger.info("Pipeline started.", extra={'extra_data': {"event": "pipeline_start", "data": {"timestamp": datetime.utcnow().isoformat()}}})

def log_pipeline_complete():
    """Log the successful completion of the pipeline."""
    logger = get_logger()
    logger.info("Pipeline completed.", extra={'extra_data': {"event": "pipeline_complete", "data": {"timestamp": datetime.utcnow().isoformat()}}})

def log_pipeline_error(error_msg: str):
    """
    Log a pipeline error.
    
    Args:
        error_msg: Error message describing the failure
    """
    logger = get_logger()
    logger.error(f"Pipeline error: {error_msg}", extra={'extra_data': {"event": "pipeline_error", "data": {"error": error_msg}}})

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
        "exclusion_rate": exclusion_rate,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger = get_logger()
    logger.info(json.dumps({
        "event": "language_exclusion_rate",
        "data": log_data
    }), extra={'extra_data': log_data})

def log_metric_calculation(metric_name: str, project_id: str, value: float):
    """
    Log a calculated metric value for pipeline monitoring.
    
    Args:
        metric_name: Name of the metric (e.g., 'response_time_variance')
        project_id: Project identifier
        value: Calculated metric value
    """
    logger = get_logger()
    log_data = {
        "metric_name": metric_name,
        "project_id": project_id,
        "value": value,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.info(json.dumps({
        "event": "metric_calculated",
        "data": log_data
    }), extra={'extra_data': log_data})

def log_bot_exclusion(project_id: str, bot_count: int, total_count: int):
    """
    Log bot exclusion statistics for a project.
    
    Args:
        project_id: Project identifier
        bot_count: Number of bot events excluded
        total_count: Total number of events processed
    """
    logger = get_logger()
    log_data = {
        "project_id": project_id,
        "bot_count": bot_count,
        "total_count": total_count,
        "exclusion_rate": bot_count / total_count if total_count > 0 else 0.0,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.info(json.dumps({
        "event": "bot_exclusion",
        "data": log_data
    }), extra={'extra_data': log_data})

def log_data_ingestion_status(project_id: str, events_loaded: int, status: str):
    """
    Log the status of data ingestion for a project.
    
    Args:
        project_id: Project identifier
        events_loaded: Number of events loaded
        status: Ingestion status ('success', 'partial', 'failed')
    """
    logger = get_logger()
    log_data = {
        "project_id": project_id,
        "events_loaded": events_loaded,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.info(json.dumps({
        "event": "ingestion_status",
        "data": log_data
    }), extra={'extra_data': log_data})