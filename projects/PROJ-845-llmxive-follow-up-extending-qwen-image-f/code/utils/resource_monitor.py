import os
import time
import threading
import platform
from contextlib import contextmanager
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class ResourceMonitor:
    """
    Monitors system resource usage (RAM) during execution.
    Supports context manager protocol.
    """
    def __init__(self):
        self._start_time: Optional[float] = None
        self._stop_time: Optional[float] = None
        self._peak_ram_gb: float = 0.0
        self._monitoring: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _get_current_ram_gb(self) -> float:
        """Get current RAM usage in GB."""
        if platform.system() == "Linux":
            # Read from /proc/self/status
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # VmRSS is in kB
                            kb = int(line.split()[1])
                            return kb / (1024 * 1024) # Convert to GB
            except Exception as e:
                logger.warning(f"Could not read /proc/self/status: {e}")
        elif platform.system() == "Darwin": # macOS
            try:
                import subprocess
                result = subprocess.run(['ps', '-o', 'rss=', '-p', str(os.getpid())], 
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    kb = int(result.stdout.strip())
                    return kb / (1024 * 1024)
            except Exception as e:
                logger.warning(f"Could not get RSS on macOS: {e}")
        elif platform.system() == "Windows":
            try:
                import psutil
                process = psutil.Process(os.getpid())
                return process.memory_info().rss / (1024 * 1024) # GB
            except ImportError:
                logger.warning("psutil not installed on Windows. Cannot measure RAM.")
            except Exception as e:
                logger.warning(f"Could not get RSS on Windows: {e}")
        
        return 0.0

    def _monitor_loop(self):
        """Background thread to monitor RAM."""
        while not self._stop_event.is_set():
            current = self._get_current_ram_gb()
            if current > self._peak_ram_gb:
                self._peak_ram_gb = current
            time.sleep(0.5) # Check every 0.5 seconds

    def start(self):
        """Start monitoring resources."""
        if self._monitoring:
            return
        
        self._start_time = time.time()
        self._peak_ram_gb = 0.0
        self._monitoring = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Resource monitoring started.")

    def stop(self):
        """Stop monitoring resources."""
        if not self._monitoring:
            return

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._stop_time = time.time()
        self._monitoring = False
        logger.info(f"Resource monitoring stopped. Peak RAM: {self._peak_ram_gb:.2f} GB")

    def get_peak_ram_gb(self) -> float:
        """Return the peak RAM usage recorded so far in GB."""
        if not self._monitoring:
            # If not monitoring, try to get a snapshot
            return self._get_current_ram_gb()
        return self._peak_ram_gb

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False # Do not suppress exceptions

@contextmanager
def monitor_resources():
    """Context manager for resource monitoring."""
    monitor = ResourceMonitor()
    try:
        monitor.start()
        yield monitor
    finally:
        monitor.stop()
# Note: The function above is a helper, but the class itself is the primary interface.
# The class implements __enter__ and __exit__ directly.