import os
import time
import logging
import json
import psutil
from typing import Optional, Dict, Any
from pathlib import Path

# Configure logging for the monitor module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ActiveMonitor:
    """
    A context manager that actively monitors memory usage and wall-clock time.
    
    It periodically samples the process's RSS (Resident Set Size) to track peak memory
    and calculates the elapsed time between entry and exit.
    
    Attributes:
        start_time (float): Timestamp when the monitor started.
        peak_memory_bytes (int): Highest RSS observed during monitoring.
        process (psutil.Process): The current process object.
        sampling_interval (float): Seconds between memory samples.
        is_monitoring (bool): Flag to control the background sampling thread.
        metrics (Dict[str, Any]): Collected metrics upon exit.
    """

    def __init__(self, sampling_interval: float = 0.1):
        """
        Initialize the monitor.
        
        Args:
            sampling_interval: Time in seconds between memory samples.
        """
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory_bytes: int = 0
        self.process = psutil.Process(os.getpid())
        self.sampling_interval = sampling_interval
        self.is_monitoring = False
        self.metrics: Dict[str, Any] = {}

    def _sample_memory(self):
        """Continuously sample memory usage until monitoring stops."""
        while self.is_monitoring:
            try:
                # Get memory info for the current process
                mem_info = self.process.memory_info()
                current_rss = mem_info.rss
                if current_rss > self.peak_memory_bytes:
                    self.peak_memory_bytes = current_rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process might have terminated or we lost access
                break
            time.sleep(self.sampling_interval)

    def __enter__(self):
        """Start the monitoring context."""
        self.start_time = time.time()
        self.is_monitoring = True
        self.peak_memory_bytes = 0
        
        # Start the background sampling thread
        import threading
        self._thread = threading.Thread(target=self._sample_memory, daemon=True)
        self._thread.start()
        
        logger.info("ActiveMonitor started.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop monitoring and record final metrics."""
        self.end_time = time.time()
        self.is_monitoring = False
        
        # Wait for the sampling thread to finish
        if hasattr(self, '_thread'):
            self._thread.join(timeout=1.0)
        
        # Calculate elapsed time
        elapsed_seconds = self.end_time - self.start_time if self.end_time and self.start_time else 0.0
        
        # Convert bytes to MB for readability
        peak_memory_mb = self.peak_memory_bytes / (1024 * 1024)
        
        self.metrics = {
            "wall_clock_time_seconds": elapsed_seconds,
            "peak_memory_bytes": self.peak_memory_bytes,
            "peak_memory_mb": round(peak_memory_mb, 2),
            "success": exc_type is None
        }
        
        logger.info(f"ActiveMonitor finished. Duration: {elapsed_seconds:.2f}s, Peak Memory: {peak_memory_mb:.2f} MB.")
        
        # Return False to propagate exceptions if any occurred
        return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Retrieve the collected metrics.
        
        Returns:
            Dictionary containing wall_clock_time_seconds, peak_memory_bytes, etc.
        """
        return self.metrics.copy()


def monitor_execution(func):
    """
    A decorator to wrap a function execution with active monitoring.
    
    This decorator ensures that the function runs within an ActiveMonitor context,
    logs the results to a specified file (or prints them if no path is provided),
    and returns the function's result.
    
    Args:
        func: The function to wrap.
        
    Returns:
        The wrapped function.
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        log_path = kwargs.pop('monitor_log_path', None)
        
        with ActiveMonitor() as monitor:
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Function {func.__name__} raised an exception: {e}")
                raise
            finally:
                metrics = monitor.get_metrics()
                
                if log_path:
                    log_file = Path(log_path)
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_file, 'a') as f:
                        entry = {
                            "function": func.__name__,
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
                            "metrics": metrics
                        }
                        f.write(json.dumps(entry) + "\n")
                    logger.info(f"Monitor metrics logged to {log_path}")
                else:
                    logger.info(f"Monitor metrics for {func.__name__}: {metrics}")
                    
        return result

    return wrapper