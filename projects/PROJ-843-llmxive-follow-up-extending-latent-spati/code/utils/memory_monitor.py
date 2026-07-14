import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from memory_profiler import memory_usage
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False

class MemoryMonitor:
    """
    Monitors memory usage and wall-clock time in a background thread.
    """
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path("data/memory_monitor_log.json")
        self._start_time: Optional[float] = None
        self._stop_time: Optional[float] = None
        self._peak_ram_mb: float = 0.0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._measurements: list = []
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the monitoring thread."""
        if self._thread and self._thread.is_alive():
            return
        self._start_time = time.time()
        self._stop_event.clear()
        self._measurements = []
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return summary."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._stop_time = time.time()
        elapsed = self._stop_time - self._start_time if self._start_time else 0
        
        summary = {
            "start_time": datetime.fromtimestamp(self._start_time).isoformat() if self._start_time else None,
            "stop_time": datetime.fromtimestamp(self._stop_time).isoformat() if self._stop_time else None,
            "elapsed_seconds": elapsed,
            "peak_ram_mb": self._peak_ram_mb,
            "measurements": self._measurements
        }

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, 'w') as f:
            json.dump(summary, f, indent=2)
        return summary

    def _monitor_loop(self) -> None:
        """Background loop to sample memory."""
        interval = 1.0
        while not self._stop_event.is_set():
            if HAS_MEMORY_PROFILER:
                try:
                    # memory_usage returns a tuple (pid, mem) or just mem depending on args
                    # Using default behavior: returns memory usage of current process
                    mem = memory_usage((os.getpid(),), interval=0.1, timeout=0.1, include_children=True)
                    # memory_usage returns a list of values over the interval
                    current_peak = max(mem) if mem else 0
                except Exception:
                    current_peak = 0
            else:
                # Fallback if memory_profiler not installed (read /proc on Linux)
                current_peak = self._get_proc_mem()

            with self._lock:
                if current_peak > self._peak_ram_mb:
                    self._peak_ram_mb = current_peak
                self._measurements.append({
                    "timestamp": time.time(),
                    "ram_mb": current_peak
                })
            
            self._stop_event.wait(interval)

    def _get_proc_mem(self) -> float:
        """Fallback memory reading for Linux."""
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        parts = line.split()
                        return float(parts[1]) / 1024.0 # Convert kB to MB
        except Exception:
            return 0.0
        return 0.0

    def info(self, msg: str) -> None:
        pass # No-op for compatibility

    def debug(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        pass

    def log(self, msg: str) -> None:
        pass

def parse_memory_logs(log_path: Optional[Path] = None) -> Dict[str, Any]:
    """Read the latest memory log file."""
    path = log_path or Path("data/memory_monitor_log.json")
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)
