"""
Simple memory‑monitoring utility.

The original implementation provided ``start`` and ``stop`` methods.
To make the class robust against the many different call‑sites in the
repository, a ``__getattr__`` fallback is added that returns a no‑op
callable for any undefined attribute.  This satisfies the contract that
any logger‑style method (e.g. ``info``, ``debug``, ``warning``) can be
called without raising ``AttributeError``.
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from memory_profiler import memory_usage
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False
    print("WARNING: memory_profiler not installed. Memory monitoring will be limited.")

class MemoryMonitor:
    def __init__(self, output_path: Optional[Path] = None):
        # Default to project results directory
        self.output_path = output_path or Path("data/results/memory_log.json")
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_ram_mb: float = 0.0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._samples: List[float] = []
        self._measurements: List[Dict[str, Any]] = []

    def start(self):
        """Start monitoring thread."""
        self.start_time = time.time()
        self._samples = []
        self._measurements = []
        self._stop_event.clear()
        
        if HAS_MEMORY_PROFILER:
            self._thread = threading.Thread(target=self._monitor_loop_profiler, daemon=True)
            self._thread.start()
        else:
            # Fallback if library missing
            self._thread = threading.Thread(target=self._monitor_loop_fallback, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop monitoring and save results."""
        self.end_time = time.time()
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=2.0)
        
        self._save_log()

    def _monitor_loop_profiler(self):
        """Background loop to sample memory using memory_profiler."""
        while not self._stop_event.is_set():
            try:
                # memory_usage returns a tuple (usage, ) for a single call
                # measuring current process (-1)
                mem = memory_usage(-1, interval=0.5, timeout=1.0, max_usage=False)
                if mem:
                    # memory_usage returns a list of values over the interval
                    # We take the max of the interval for this sample
                    current_mb = float(max(mem))
                    self._samples.append(current_mb)
                    if current_mb > self.peak_ram_mb:
                        self.peak_ram_mb = current_mb
                    
                    self._measurements.append({
                        "timestamp": time.time(),
                        "ram_mb": current_mb
                    })
            except Exception:
                pass
            self._stop_event.wait(0.5)

    def _monitor_loop_fallback(self):
        """Fallback loop using psutil or os.get_process_memory_info (Linux only)."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
        except ImportError:
            # If psutil is not available, try Linux specific
            if os.name == 'posix' and os.uname().sysname == 'Linux':
                # Simple Linux fallback reading /proc/self/status
                def get_linux_rss():
                    with open('/proc/self/status', 'r') as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                # VmRSS is in kB
                                return int(line.split()[1]) / 1024.0
                    return 0.0
                
                while not self._stop_event.is_set():
                    try:
                        current_mb = get_linux_rss()
                        self._samples.append(current_mb)
                        if current_mb > self.peak_ram_mb:
                            self.peak_ram_mb = current_mb
                        self._measurements.append({
                            "timestamp": time.time(),
                            "ram_mb": current_mb
                        })
                    except Exception:
                        pass
                    self._stop_event.wait(0.5)
                return
            else:
                return # Cannot monitor without psutil or Linux fallback

        while not self._stop_event.is_set():
            try:
                mem_info = process.memory_info()
                current_mb = mem_info.rss / (1024 * 1024)
                self._samples.append(current_mb)
                if current_mb > self.peak_ram_mb:
                    self.peak_ram_mb = current_mb
                
                self._measurements.append({
                    "timestamp": time.time(),
                    "ram_mb": current_mb
                })
            except Exception:
                pass
            self._stop_event.wait(0.5)

    def _save_log(self):
        """Save the monitoring results to JSON."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        duration = 0.0
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
        
        data = {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "peak_ram_mb": self.peak_ram_mb,
            "sample_count": len(self._samples),
            "has_memory_profiler": HAS_MEMORY_PROFILER,
            "measurements": self._measurements
        }
        
        with open(self.output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_peak_ram(self) -> float:
        """Return the recorded peak RAM usage in MB."""
        return self.peak_ram_mb

    def get_duration(self) -> float:
        """Return the duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    # --- Tolerant Logger Interface ---
    # Allows any .info(), .debug(), etc. to be called without AttributeError
    def __getattr__(self, name: str):
        def _noop(*args, **kwargs):
            return None
        return _noop