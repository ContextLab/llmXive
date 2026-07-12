import os
import json
import time
import threading
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from src.utils.config import get_path, get_config

# Global logger instance and thread
_logger_instance: Optional["ResourceLogger"] = None
_logging_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()

class ResourceLogger:
    """
    Logs RAM, CPU usage, and custom metrics to JSON files.
    Supports interval-based sampling and custom metric logging.
    """
    def __init__(self, output_dir: str = "results", filename_prefix: str = "metrics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.filename_prefix = filename_prefix
        self.metrics_buffer: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.interval = 1.0  # Default 1 second
        
        # Initialize logging for the module
        self.log = logging.getLogger(__name__)

    def start_sampling(self, interval: float = 1.0):
        """Start the background thread for resource sampling."""
        self.interval = interval
        if _logging_thread is not None and _logging_thread.is_alive():
            return
        
        _stop_event.clear()
        thread = threading.Thread(target=self._sampling_loop, daemon=True)
        thread.start()
        _logging_thread = thread
        self.log.info(f"Resource logging started with {interval}s interval")

    def _sampling_loop(self):
        """Background loop to sample system resources."""
        while not _stop_event.is_set():
            metrics = {
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(interval=None),
                "ram_percent": psutil.virtual_memory().percent,
                "ram_used_mb": psutil.virtual_memory().used / (1024 * 1024)
            }
            self.log_metrics(metrics)
            _stop_event.wait(self.interval)

    def log_metrics(self, metrics: Dict[str, Any]):
        """
        Add metrics to the buffer. If called directly (not from thread),
        it writes immediately. If from thread, it buffers periodically.
        For this implementation, we write immediately to ensure data capture
        for baseline runs, but structure allows buffering.
        """
        timestamped = {
            "timestamp": time.time(),
            **metrics
        }
        
        with self.lock:
            self.metrics_buffer.append(timestamped)
            # Flush to disk periodically or on every call to ensure persistence
            # For baseline runs, we flush immediately to avoid data loss on crash
            self._flush()

    def _flush(self):
        """Write buffer to disk."""
        if not self.metrics_buffer:
            return
        
        filepath = self.output_dir / f"{self.filename_prefix}_{int(time.time())}.json"
        try:
            with open(filepath, 'w') as f:
                json.dump(self.metrics_buffer, f, indent=2)
            self.metrics_buffer.clear()
        except Exception as e:
            self.log.error(f"Failed to write metrics to {filepath}: {e}")

    def stop_sampling(self):
        """Stop the background sampling thread."""
        _stop_event.set()
        if _logging_thread is not None:
            _logging_thread.join(timeout=2.0)
        self._flush()  # Ensure final data is written

def get_logger() -> ResourceLogger:
    global _logger_instance
    if _logger_instance is None:
        output_dir = get_path("results")
        _logger_instance = ResourceLogger(output_dir)
    return _logger_instance

def log_metrics(metrics: Dict[str, Any]):
    """
    Convenience function to log metrics using the global logger instance.
    Used for logging baseline path optimality ratios and success rates.
    """
    logger = get_logger()
    logger.log_metrics(metrics)

def start_logging(interval: float = 1.0):
    """Start the global resource logging thread."""
    logger = get_logger()
    logger.start_sampling(interval)

def stop_logging():
    """Stop the global resource logging thread."""
    logger = get_logger()
    logger.stop_sampling()

def get_resource_summary() -> Dict[str, float]:
    """Get a snapshot of current resource usage."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent,
        "ram_used_mb": psutil.virtual_memory().used / (1024 * 1024)
    }
