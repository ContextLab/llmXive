"""
Structured logging and resource usage tracking for llmXive.

This module provides:
1. A structured logger that outputs JSON-formatted logs.
2. Periodic memory (RAM) and CPU usage tracking via a background thread.
3. Integration with the project's config system.
"""

import json
import logging
import os
import platform
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import psutil

# Import project config to ensure consistency
# Note: Assuming utils.config is in the same package or accessible via PYTHONPATH
from .config import get_default_config


class ResourceMonitor:
    """
    Background thread that periodically logs memory and CPU usage.
    Stops gracefully when the main thread exits or stop() is called.
    """

    def __init__(self, logger: logging.Logger, interval_seconds: float = 10.0, warning_threshold_gb: float = 6.5):
        self.logger = logger
        self.interval = interval_seconds
        self.warning_threshold_gb = warning_threshold_gb
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.process = psutil.Process(os.getpid())

    def _get_usage(self) -> Tuple[float, float]:
        """Returns (memory_mb, cpu_percent)"""
        mem_info = self.process.memory_info()
        mem_mb = mem_info.rss / (1024 * 1024)
        cpu_pct = self.process.cpu_percent()
        return mem_mb, cpu_pct

    def _run(self):
        while not self._stop_event.is_set():
            mem_mb, cpu_pct = self._get_usage()
            mem_gb = mem_mb / 1024.0

            log_entry = {
                "event": "resource_usage",
                "timestamp": datetime.utcnow().isoformat(),
                "memory_mb": round(mem_mb, 2),
                "memory_gb": round(mem_gb, 4),
                "cpu_percent": round(cpu_pct, 2),
                "platform": platform.platform(),
                "python_version": platform.python_version()
            }

            # Log at INFO level normally
            self.logger.info("Resource Usage", extra={"resource": log_entry})

            # Check thresholds and log warning if exceeded
            if mem_gb > self.warning_threshold_gb:
                self.logger.warning(
                    f"Memory usage ({mem_gb:.2f} GB) exceeds threshold ({self.warning_threshold_gb} GB)",
                    extra={"resource": log_entry}
                )

            # Wait for interval or stop signal
            self._stop_event.wait(self.interval)

    def start(self):
        """Start the background monitoring thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the background monitoring thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines.
    Adds standard fields: timestamp, level, logger, message, and extra data.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
        }

        # Add extra fields if present
        if hasattr(record, "resource"):
            log_data["resource"] = record.resource
        
        # Handle exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


def get_structured_logger(
    name: str = "llmxive",
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_resource_monitor: bool = True,
    resource_interval: float = 10.0,
    warning_threshold_gb: float = 6.5
) -> Tuple[logging.Logger, Optional[ResourceMonitor]]:
    """
    Create a structured logger with optional resource monitoring.

    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (e.g., logging.INFO)
        log_file: Optional path to log file. If None, logs to stdout.
        enable_resource_monitor: If True, starts a background thread to track RAM/CPU.
        resource_interval: Interval in seconds for resource checks.
        warning_threshold_gb: Memory threshold (GB) to trigger a warning log.

    Returns:
        Tuple of (logger, resource_monitor_instance).
        resource_monitor is None if enable_resource_monitor is False.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        # Create formatter
        formatter = StructuredFormatter()

        # Handler for file or stdout
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler(sys.stdout)
        
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        logger.addHandler(handler)

    resource_monitor = None
    if enable_resource_monitor:
        resource_monitor = ResourceMonitor(
            logger, 
            interval_seconds=resource_interval, 
            warning_threshold_gb=warning_threshold_gb
        )
        resource_monitor.start()

    return logger, resource_monitor


def get_logger_for_task(task_id: str, log_dir: str = "data/logs") -> Tuple[logging.Logger, Optional[ResourceMonitor]]:
    """
    Convenience function to get a logger for a specific task, saving logs to data/logs.
    
    Args:
        task_id: The task identifier (e.g., "T005")
        log_dir: Directory to store logs.
        
    Returns:
        Tuple of (logger, resource_monitor)
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{task_id}.log")
    
    return get_structured_logger(
        name=f"llmxive.{task_id}",
        log_file=log_file,
        enable_resource_monitor=True
    )


# Convenience function to get a global logger instance for the project
_global_logger: Optional[logging.Logger] = None
_global_monitor: Optional[ResourceMonitor] = None

def get_global_logger() -> Tuple[logging.Logger, ResourceMonitor]:
    """
    Returns a singleton global logger and resource monitor for the project.
    Initializes on first call.
    """
    global _global_logger, _global_monitor
    if _global_logger is None:
        _global_logger, _global_monitor = get_structured_logger(
            name="llmxive.global",
            log_level=logging.INFO,
            enable_resource_monitor=True
        )
    return _global_logger, _global_monitor