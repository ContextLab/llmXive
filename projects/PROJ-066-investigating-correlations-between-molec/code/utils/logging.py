"""
Logging utilities for structured logging and resource monitoring.
"""
import logging
import sys
import json
import time
import threading
import traceback
from pathlib import Path
from typing import Optional

# Project root
project_root = Path(__file__).resolve().parent.parent.parent
LOG_DIR = project_root / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter to output logs as JSON for structured logging.
    """
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Gets a logger with structured formatting.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        logger.addHandler(console_handler)
        
        # File handler
        log_file = LOG_DIR / f"{name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    return logger

def log_pipeline_step(task_id: str, step_name: str, status: str = "started", details: Optional[dict] = None) -> None:
    """
    Logs a pipeline step with structured information.
    """
    logger = get_logger("pipeline")
    log_data = {
        "task_id": task_id,
        "step": step_name,
        "status": status,
        "details": details or {}
    }
    logger.info(f"Pipeline Step: {json.dumps(log_data)}")

class ResourceMonitor:
    """
    Monitors memory and CPU usage during execution.
    """
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.peak_memory = 0
        self._monitoring = False
        self._thread = None
        self.logger = get_logger("resource_monitor")

    def start(self):
        """Starts the resource monitoring thread."""
        self.start_time = time.time()
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self.logger.info("Resource monitoring started.")

    def stop(self):
        """Stops the resource monitoring thread."""
        self._monitoring = False
        self.end_time = time.time()
        if self._thread:
            self._thread.join(timeout=1.0)
        self.logger.info(f"Resource monitoring stopped. Duration: {self.get_duration():.2f}s, Peak Memory: {self.peak_memory:.2f} MB")

    def _monitor_loop(self):
        """Background loop to check resource usage."""
        try:
            import psutil
            process = psutil.Process()
            while self._monitoring:
                memory_info = process.memory_info().rss / (1024 * 1024)  # MB
                if memory_info > self.peak_memory:
                    self.peak_memory = memory_info
                time.sleep(1.0)
        except ImportError:
            # psutil not installed, skip monitoring
            self._monitoring = False
        except Exception as e:
            self.logger.error(f"Error in resource monitor: {e}")
            self._monitoring = False

    def get_duration(self) -> float:
        """Returns the duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0

    def get_peak_memory_mb(self) -> float:
        """Returns the peak memory usage in MB."""
        return self.peak_memory

def log_resource_usage(logger_name: str, memory_mb: float, duration_s: float) -> None:
    """
    Logs resource usage metrics.
    """
    logger = get_logger(logger_name)
    logger.info(f"Resource Usage - Memory: {memory_mb:.2f} MB, Duration: {duration_s:.2f} s")

def start_monitoring() -> ResourceMonitor:
    """
    Convenience function to start a new ResourceMonitor.
    """
    monitor = ResourceMonitor()
    monitor.start()
    return monitor
