"""
Logging infrastructure for tracking API success/failure rates.

Implements FR-009: Track API success/failure rates with structured logging.
"""
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import threading

# Global registry for API metrics
_api_metrics_lock = threading.Lock()
_api_metrics: Dict[str, Dict[str, int]] = {}

def _get_metrics_for_service(service_name: str) -> Dict[str, int]:
    """Get or initialize metrics for a specific service."""
    with _api_metrics_lock:
        if service_name not in _api_metrics:
            _api_metrics[service_name] = {"success": 0, "failure": 0}
        return _api_metrics[service_name]

def log_api_call(service_name: str, success: bool) -> None:
    """
    Log an API call result for tracking success/failure rates.
    
    Args:
        service_name: Name of the API service (e.g., 'npm', 'github', 'audit')
        success: True if the call succeeded, False otherwise
    """
    metrics = _get_metrics_for_service(service_name)
    if success:
        metrics["success"] += 1
    else:
        metrics["failure"] += 1

def get_api_success_rate(service_name: str) -> Optional[float]:
    """
    Calculate the success rate for a specific service.
    
    Args:
        service_name: Name of the API service
        
    Returns:
        Success rate as a float between 0.0 and 1.0, or None if no data
    """
    with _api_metrics_lock:
        if service_name not in _api_metrics:
            return None
        metrics = _api_metrics[service_name]
        total = metrics["success"] + metrics["failure"]
        if total == 0:
            return None
        return metrics["success"] / total

def get_all_api_metrics() -> Dict[str, Dict[str, Any]]:
    """
    Get a snapshot of all API metrics.
    
    Returns:
        Dictionary mapping service names to their metrics and success rates
    """
    with _api_metrics_lock:
        result = {}
        for service_name, metrics in _api_metrics.items():
            total = metrics["success"] + metrics["failure"]
            success_rate = metrics["success"] / total if total > 0 else None
            result[service_name] = {
                "success": metrics["success"],
                "failure": metrics["failure"],
                "total": total,
                "success_rate": success_rate
            }
        return result

def reset_api_metrics() -> None:
    """Reset all API metrics. Useful for testing or fresh runs."""
    global _api_metrics
    with _api_metrics_lock:
        _api_metrics = {}

def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    service_name: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger with appropriate handlers.
    
    Args:
        log_file: Optional path to write logs to (default: stdout only)
        level: Logging level (default: INFO)
        service_name: Optional service name for log formatting
        
    Returns:
        Configured logger instance
    """
    logger_name = f"npm_analysis.{service_name}" if service_name else "npm_analysis"
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Formatter with timestamp and service info
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def export_metrics_report(output_path: Path) -> None:
    """
    Export current API metrics to a JSON file.
    
    Args:
        output_path: Path to write the metrics report
    """
    metrics = get_all_api_metrics()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": metrics
        }, f, indent=2)

# Convenience logger instance for general use
_default_logger: Optional[logging.Logger] = None

def get_logger(service_name: Optional[str] = None) -> logging.Logger:
    """Get the default logger, creating it if necessary."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging(service_name=service_name)
    elif service_name:
        # Return a service-specific logger if requested
        return logging.getLogger(f"npm_analysis.{service_name}")
    return _default_logger