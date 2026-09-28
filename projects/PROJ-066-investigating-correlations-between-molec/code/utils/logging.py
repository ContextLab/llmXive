"""
Structured logging and resource monitoring utilities.
"""
import logging
import sys
import json
import time
import threading
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = traceback.format_exception(*record.exc_info)
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with structured formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
    return logger

def log_pipeline_step(task_id: str, step_name: str, status: str = "in_progress") -> None:
    """Log a pipeline step with task ID."""
    logger = get_logger(__name__)
    logger.info(f"[{task_id}] {step_name} - Status: {status}")

class ResourceMonitor:
    """Monitor memory and CPU usage."""
    def __init__(self):
        self.start_time = None
        self.peak_memory = 0
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Start monitoring."""
        self.start_time = time.time()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger = get_logger(__name__)
        logger.info("Resource monitoring started.")

    def stop(self):
        """Stop monitoring."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        logger = get_logger(__name__)
        logger.info(f"Resource monitoring stopped. Peak memory: {self.peak_memory} MB")

    def _monitor_loop(self):
        """Periodically check memory usage."""
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            # Fallback if psutil not available
            return

        while not self._stop_event.is_set():
            try:
                mem_mb = process.memory_info().rss / (1024 * 1024)
                if mem_mb > self.peak_memory:
                    self.peak_memory = mem_mb
                self._stop_event.wait(10)  # Check every 10 seconds
            except Exception:
                break

def log_resource_usage() -> dict:
    """Log current resource usage."""
    logger = get_logger(__name__)
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent()
        logger.info(f"Memory: {mem_mb:.2f} MB, CPU: {cpu_percent:.2f}%")
        return {"memory_mb": mem_mb, "cpu_percent": cpu_percent}
    except ImportError:
        logger.warning("psutil not available for resource logging.")
        return {}

def start_monitoring():
    """Start the global resource monitor."""
    return ResourceMonitor()
