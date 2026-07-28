import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

# Constants for log levels and formats
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global registry for API metrics
_api_metrics_registry: Dict[str, Dict[str, int]] = {}

def get_api_logger(name: str = "api_monitor") -> logging.Logger:
    """
    Creates or retrieves a logger configured for API monitoring.
    This logger tracks success/failure rates as per FR-009.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)

    # File handler for API logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "api_activity.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def log_api_call(
    logger: logging.Logger,
    service: str,
    endpoint: str,
    status: str,
    duration_ms: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs an API call outcome to the standard logger and updates the metrics registry.
    status should be 'SUCCESS' or 'FAILURE'.
    """
    # Update metrics registry
    key = f"{service}:{endpoint}"
    if key not in _api_metrics_registry:
        _api_metrics_registry[key] = {"success": 0, "failure": 0}

    if status == "SUCCESS":
        _api_metrics_registry[key]["success"] += 1
        log_level = logging.INFO
        msg = f"API Call Success: {service} -> {endpoint}"
    elif status == "FAILURE":
        _api_metrics_registry[key]["failure"] += 1
        log_level = logging.WARNING
        msg = f"API Call Failure: {service} -> {endpoint}"
    else:
        log_level = logging.INFO
        msg = f"API Call ({status}): {service} -> {endpoint}"

    log_data = {"service": service, "endpoint": endpoint, "status": status}
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    if extra:
        log_data.update(extra)

    logger.log(log_level, msg, extra=log_data)

def get_aggregated_metrics() -> Dict[str, Dict[str, Any]]:
    """
    Returns the current aggregated success/failure counts for all tracked endpoints.
    """
    return dict(_api_metrics_registry)

def calculate_success_ratio(service: str, endpoint: str) -> Optional[float]:
    """
    Calculates the success ratio for a specific service/endpoint.
    Returns None if no data exists.
    """
    key = f"{service}:{endpoint}"
    if key not in _api_metrics_registry:
        return None

    stats = _api_metrics_registry[key]
    total = stats["success"] + stats["failure"]
    if total == 0:
        return None

    return stats["success"] / total

def reset_metrics() -> None:
    """
    Clears the in-memory metrics registry. Useful for testing or periodic resets.
    """
    global _api_metrics_registry
    _api_metrics_registry = {}
