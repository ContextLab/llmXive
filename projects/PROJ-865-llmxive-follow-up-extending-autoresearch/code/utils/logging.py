import logging
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Ensure consistent log directory structure
LOG_DIR = Path(__file__).parent.parent.parent / "data" / "artifacts"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with structured output."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler for persistent logs
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        log_filename = f"{name}_{timestamp}.log"
        log_path = LOG_DIR / log_filename
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        # Store log path in logger for reference
        logger.log_path = str(log_path)
        
    return logger

def log_stage_start(stage_name: str, input_path: str, output_path: str):
    """Log the start of a pipeline stage with structured metadata."""
    logger = get_logger(stage_name)
    log_entry = {
        "event": "stage_start",
        "stage_name": stage_name,
        "input_path": input_path,
        "output_path": output_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid()
    }
    logger.info(json.dumps(log_entry))
    logger.info(f"--- Stage Start: {stage_name} ---")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

def log_stage_end(stage_name: str, success: bool, details: Optional[Dict[str, Any]] = None):
    """Log the end of a pipeline stage with structured metadata."""
    logger = get_logger(stage_name)
    status = "SUCCESS" if success else "FAILURE"
    log_entry = {
        "event": "stage_end",
        "stage_name": stage_name,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid()
    }
    if details:
        log_entry["details"] = details
    
    logger.info(json.dumps(log_entry))
    logger.info(f"--- Stage End: {stage_name} - {status} ---")
    if details:
        logger.info(f"Details: {json.dumps(details)}")

def log_resource_usage():
    """Log current resource usage (CPU and Memory) with structured format."""
    logger = get_logger("resource_monitor")
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=0.1)
        
        log_entry = {
            "event": "resource_usage",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "memory_mb": round(mem_info.rss / 1024 / 1024, 2),
            "memory_percent": round(process.memory_percent(), 2),
            "cpu_percent": round(cpu_percent, 2)
        }
        logger.info(json.dumps(log_entry))
        logger.info(f"Current Memory Usage: {log_entry['memory_mb']:.2f} MB ({log_entry['memory_percent']:.2f}%)")
        logger.info(f"Current CPU Usage: {log_entry['cpu_percent']:.2f}%")
    except ImportError:
        logger.warning("psutil not installed, skipping resource log.")
    except Exception as e:
        logger.error(f"Error logging resource usage: {str(e)}")

def log_metric(stage_name: str, metric_name: str, value: float, unit: str = "count"):
    """Log a specific metric with structured format."""
    logger = get_logger(stage_name)
    log_entry = {
        "event": "metric",
        "stage_name": stage_name,
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid()
    }
    logger.info(json.dumps(log_entry))
    logger.info(f"Metric: {metric_name} = {value} {unit}")

def log_error(stage_name: str, error_message: str, error_type: str = "Unknown"):
    """Log an error with structured format."""
    logger = get_logger(stage_name)
    log_entry = {
        "event": "error",
        "stage_name": stage_name,
        "error_type": error_type,
        "error_message": error_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid()
    }
    logger.error(json.dumps(log_entry))
    logger.error(f"Error [{error_type}]: {error_message}")

def log_debug(stage_name: str, message: str):
    """Log a debug message."""
    logger = get_logger(stage_name)
    logger.debug(message)

def log_info(stage_name: str, message: str):
    """Log an info message."""
    logger = get_logger(stage_name)
    logger.info(message)

def log_warning(stage_name: str, message: str):
    """Log a warning message."""
    logger = get_logger(stage_name)
    logger.warning(message)

def log_critical(stage_name: str, message: str):
    """Log a critical message."""
    logger = get_logger(stage_name)
    logger.critical(message)