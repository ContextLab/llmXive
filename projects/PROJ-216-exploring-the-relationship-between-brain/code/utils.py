import json
import os
import sys
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import psutil
except ImportError:
    psutil = None
    print("Warning: psutil not installed. Resource monitoring will be limited.", file=sys.stderr)

class ResourceUsage:
    def __init__(self, timestamp: float, ram_gb: float, cpu_percent: float):
        self.timestamp = timestamp
        self.ram_gb = ram_gb
        self.cpu_percent = cpu_percent

class ResourceMonitor:
    """
    Monitors RAM and CPU usage for a subject processing task.
    Logs usage to stderr and writes a summary JSON to data/processed/resource_profile.json.
    """
    def __init__(self, processed_dir: Optional[str] = None):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.usage_samples: List[ResourceUsage] = []
        # Default to project standard, but allow override for testing
        if processed_dir:
            self.output_path = str(Path(processed_dir) / "resource_profile.json")
        else:
            self.output_path = "data/processed/resource_profile.json"
        self._process = None
        self._interval = 0.1  # Sample every 100ms
        self._monitoring = False
        self._samples_thread: Optional[threading.Thread] = None

    def _get_current_usage(self) -> Optional[ResourceUsage]:
        if psutil is None:
            return None
        try:
            if self._process is None:
                self._process = psutil.Process(os.getpid())
            
            mem_info = self._process.memory_info()
            ram_gb = mem_info.rss / (1024 ** 3)
            cpu_pct = self._process.cpu_percent()
            
            return ResourceUsage(
                timestamp=time.time(),
                ram_gb=ram_gb,
                cpu_percent=cpu_pct
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def _monitoring_loop(self):
        """Background loop to sample resource usage."""
        while self._monitoring:
            sample = self._get_current_usage()
            if sample:
                self.usage_samples.append(sample)
            time.sleep(self._interval)

    def start(self):
        """Starts the resource monitoring loop."""
        if psutil is None:
            sys.stderr.write("[ResourceMonitor] psutil not available. Skipping monitoring.\n")
            self.start_time = time.time()
            return

        self.start_time = time.time()
        self.usage_samples = []
        self._process = None # Reset process reference
        self._monitoring = True
        
        # Start background sampling thread
        self._samples_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._samples_thread.start()
        
        # Initial sample
        sample = self._get_current_usage()
        if sample:
            self.usage_samples.append(sample)
            sys.stderr.write(f"[ResourceMonitor] Started monitoring. Initial RAM: {sample.ram_gb:.2f} GB\n")

    def stop(self):
        """Stops the resource monitoring loop."""
        self._monitoring = False
        if self._samples_thread:
            self._samples_thread.join(timeout=1.0)
        
        self.end_time = time.time()
        # Final sample
        sample = self._get_current_usage()
        if sample:
            self.usage_samples.append(sample)
            sys.stderr.write(f"[ResourceMonitor] Stopped monitoring. Final RAM: {sample.ram_gb:.2f} GB\n")

    def finalize(self):
        """
        Calculates peak RAM and total runtime, then writes the JSON profile.
        """
        if not self.start_time:
            self.start_time = time.time()
        if not self.end_time:
            self.end_time = time.time()

        total_runtime_seconds = self.end_time - self.start_time
        total_runtime_hours = total_runtime_seconds / 3600.0

        peak_ram_gb = 0.0
        if self.usage_samples:
            peak_ram_gb = max(s.ram_gb for s in self.usage_samples)

        profile = {
            "peak_ram_gb": float(peak_ram_gb),
            "total_runtime_hours": float(total_runtime_hours)
        }

        # Ensure directory exists
        out_path = Path(self.output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, 'w') as f:
            json.dump(profile, f, indent=2)

        sys.stderr.write(f"[ResourceMonitor] Finalized. Peak RAM: {peak_ram_gb:.2f} GB, Runtime: {total_runtime_hours:.4f} hours. Saved to {self.output_path}\n")
        return profile