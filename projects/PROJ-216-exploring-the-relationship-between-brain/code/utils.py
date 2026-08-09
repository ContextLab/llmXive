import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

class ResourceUsage:
    """Data class to store resource usage snapshot."""
    def __init__(self, subject_id: str, ram_gb: float, timestamp: float):
        self.subject_id = subject_id
        self.ram_gb = ram_gb
        self.timestamp = timestamp

class ResourceMonitor:
    """
    Monitors RAM usage per subject and writes aggregated profile to disk.
    """
    def __init__(self):
        self.snapshots: List[ResourceUsage] = []
        self.start_time: Optional[float] = None
        self.subject_start_times: Dict[str, float] = {}
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_current_ram_gb(self) -> float:
        """
        Get current RAM usage in GB.
        Tries to read from /proc/self/status on Linux, falls back to psutil if available,
        otherwise returns 0.0.
        """
        try:
            if sys.platform == "linux":
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # VmRSS is in kB
                            value = int(line.split()[1])
                            return value / (1024 * 1024) # Convert kB to GB
            # Fallback to psutil if available
            try:
                import psutil
                process = psutil.Process(os.getpid())
                return process.memory_info().rss / (1024 * 1024)
            except ImportError:
                pass
        except Exception:
            pass
        return 0.0

    def start(self, subject_id: str):
        """Start monitoring for a subject."""
        self.subject_start_times[subject_id] = time.time()
        if self.start_time is None:
            self.start_time = time.time()
        self.log_snapshot(subject_id)

    def stop(self, subject_id: str, error: Optional[str] = None):
        """Stop monitoring for a subject."""
        if subject_id in self.subject_start_times:
            del self.subject_start_times[subject_id]
        self.log_snapshot(subject_id)
        if error:
            print(f"[ResourceMonitor] Error for {subject_id}: {error}", file=sys.stderr)

    def log_snapshot(self, subject_id: str):
        """Log a RAM snapshot for the current subject."""
        ram = self._get_current_ram_gb()
        snapshot = ResourceUsage(subject_id, ram, time.time())
        self.snapshots.append(snapshot)
        # Log to stderr for immediate visibility
        print(f"[ResourceMonitor] {subject_id}: RAM usage = {ram:.2f} GB", file=sys.stderr)

    def finalize(self):
        """
        Finalize monitoring and write the resource profile to JSON.
        """
        if not self.snapshots:
            # No data collected, write empty profile
            profile = {
                "peak_ram_gb": 0.0,
                "total_runtime_hours": 0.0,
                "subject_count": 0,
                "snapshots": []
            }
        else:
            peak_ram = max(s.ram_gb for s in self.snapshots)
            total_runtime = 0.0
            if self.start_time:
                total_runtime = (time.time() - self.start_time) / 3600.0
            
            # Aggregate by subject to find peak per subject
            subject_peaks = {}
            for s in self.snapshots:
                if s.subject_id not in subject_peaks:
                    subject_peaks[s.subject_id] = s.ram_gb
                else:
                    subject_peaks[s.subject_id] = max(subject_peaks[s.subject_id], s.ram_gb)
            
            profile = {
                "peak_ram_gb": float(peak_ram),
                "total_runtime_hours": float(total_runtime),
                "subject_count": len(subject_peaks),
                "subject_peak_ram_gb": {k: float(v) for k, v in subject_peaks.items()},
                "snapshots": [
                    {
                        "subject_id": s.subject_id,
                        "ram_gb": float(s.ram_gb),
                        "timestamp": float(s.timestamp)
                    }
                    for s in self.snapshots
                ]
            }
        
        output_path = self.processed_dir / "resource_profile.json"
        with open(output_path, 'w') as f:
            json.dump(profile, f, indent=2)
        
        print(f"[ResourceMonitor] Profile written to {output_path}", file=sys.stderr)
