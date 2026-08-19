import os
import time
import threading
import platform
from contextlib import contextmanager
from typing import Optional

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger("resource_monitor")

class ResourceMonitor:
    """Monitor RAM usage and runtime."""
    
    def __init__(self):
        self.start_time = None
        self.peak_ram_gb = 0.0
        self._monitoring = False
        self._thread = None
    
    def start(self):
        """Start monitoring resources."""
        self.start_time = time.time()
        self.peak_ram_gb = 0.0
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Resource monitoring started")
    
    def stop(self):
        """Stop monitoring resources."""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info(f"Resource monitoring stopped. Peak RAM: {self.peak_ram_gb:.2f}GB")
    
    def get_peak_ram_gb(self) -> float:
        """Get the peak RAM usage in GB."""
        return self.peak_ram_gb
    
    def _monitor_loop(self):
        """Background thread to monitor RAM usage."""
        while self._monitoring:
            try:
                current_ram = self._get_current_ram_gb()
                if current_ram > self.peak_ram_gb:
                    self.peak_ram_gb = current_ram
            except Exception as e:
                logger.warning(f"Error monitoring RAM: {e}")
            time.sleep(1.0)
    
    def _get_current_ram_gb(self) -> float:
        """Get current RAM usage for this process."""
        if platform.system() == "Windows":
            # Windows implementation
            try:
                import psutil
                process = psutil.Process(os.getpid())
                return process.memory_info().rss / (1024 ** 3)
            except ImportError:
                return 0.0
        else:
            # Linux/Mac implementation
            try:
                with open(f'/proc/{os.getpid()}/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # VmRSS is in kB
                            rss_kb = int(line.split()[1])
                            return rss_kb / (1024 ** 2)
            except Exception:
                return 0.0
        return 0.0

@contextmanager
def monitor_resources(timeout_hours: float = 6.0):
    """Context manager for monitoring resources."""
    monitor = ResourceMonitor()
    monitor.start()
    try:
        yield monitor
    finally:
        monitor.stop()
        elapsed_hours = (time.time() - monitor.start_time) / 3600.0
        if elapsed_hours > timeout_hours:
            raise TimeoutError(f"Runtime limit exceeded: {elapsed_hours:.2f}h > {timeout_hours}h")
        if monitor.get_peak_ram_gb() > 7.0:
            raise MemoryError(f"RAM limit exceeded: {monitor.get_peak_ram_gb():.2f}GB > 7GB")
