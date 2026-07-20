"""
Utility functions and classes for the llmXive pipeline.

Includes:
- ResourceMonitor: Tracks RAM usage per subject and logs to stderr + JSON.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class ResourceUsage:
    """Container for resource usage metrics of a single subject."""
    subject_id: str
    peak_ram_mb: float
    start_time: str
    end_time: str
    duration_seconds: float

class ResourceMonitor:
    """
    Monitors RAM usage for specific subjects during processing.

    Logs usage to stderr in real-time and aggregates results to a JSON file
    in data/processed/resource_profile.json.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the monitor.

        Args:
            output_dir: Directory to write resource_profile.json. Defaults to data/processed/.
        """
        if output_dir is None:
            output_dir = Path("data/processed")
        
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "resource_profile.json"
        
        self._measurements: List[Dict[str, Any]] = []
        self._start_time: Optional[float] = None
        self._peak_ram_mb: float = 0.0
        self._current_subject: Optional[str] = None

    def _get_current_ram_mb(self) -> float:
        """Get current process RAM usage in MB."""
        if not PSUTIL_AVAILABLE:
            # Fallback to /proc on Linux if psutil missing
            if sys.platform.startswith('linux'):
                try:
                    with open('/proc/self/status', 'r') as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                # VmRSS is in kB
                                return float(line.split()[1]) / 1024.0
                except Exception:
                    pass
            return 0.0
        
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    def start_subject(self, subject_id: str) -> None:
        """
        Start monitoring for a specific subject.

        Args:
            subject_id: Unique identifier for the subject.
        """
        self._current_subject = subject_id
        self._start_time = time.time()
        self._peak_ram_mb = self._get_current_ram_mb()
        sys.stderr.write(f"[ResourceMonitor] Started monitoring for subject: {subject_id}\n")

    def record_checkpoint(self, label: str = "") -> None:
        """
        Record a checkpoint with current RAM usage.

        Args:
            label: Optional label for the checkpoint (e.g., 'preprocessing_start').
        """
        if self._current_subject is None:
            return

        current_ram = self._get_current_ram_mb()
        if current_ram > self._peak_ram_mb:
            self._peak_ram_mb = current_ram

        if label:
            sys.stderr.write(f"[ResourceMonitor] {self._current_subject} @ {label}: {current_ram:.2f} MB\n")

    def finish_subject(self) -> None:
        """
        Finish monitoring for the current subject and save the record.
        """
        if self._current_subject is None:
            sys.stderr.write("[ResourceMonitor] No active subject to finish.\n")
            return

        if self._start_time is None:
            return

        end_time = time.time()
        duration = end_time - self._start_time

        # Final check for peak
        current_ram = self._get_current_ram_mb()
        if current_ram > self._peak_ram_mb:
            self._peak_ram_mb = current_ram

        record = {
            "subject_id": self._current_subject,
            "peak_ram_mb": round(self._peak_ram_mb, 2),
            "start_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self._start_time)),
            "end_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(end_time)),
            "duration_seconds": round(duration, 2)
        }

        self._measurements.append(record)
        sys.stderr.write(f"[ResourceMonitor] Finished {self._current_subject}. Peak RAM: {self._peak_ram_mb:.2f} MB\n")
        
        # Reset state
        self._current_subject = None
        self._start_time = None
        self._peak_ram_mb = 0.0

    def save_profile(self) -> Path:
        """
        Save all collected measurements to the JSON profile file.
        
        Returns:
            Path to the saved file.
        """
        profile = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "total_subjects": len(self._measurements),
            "measurements": self._measurements
        }

        with open(self.output_file, 'w') as f:
            json.dump(profile, f, indent=2)
        
        sys.stderr.write(f"[ResourceMonitor] Profile saved to {self.output_file}\n")
        return self.output_file

    def get_summary(self) -> Dict[str, float]:
        """
        Calculate summary statistics for all recorded subjects.
        
        Returns:
            Dict with 'avg_peak_ram_mb', 'max_peak_ram_mb', 'total_duration_seconds'.
        """
        if not self._measurements:
            return {
                "avg_peak_ram_mb": 0.0,
                "max_peak_ram_mb": 0.0,
                "total_duration_seconds": 0.0
            }

        peaks = [m["peak_ram_mb"] for m in self._measurements]
        durations = [m["duration_seconds"] for m in self._measurements]

        return {
            "avg_peak_ram_mb": round(sum(peaks) / len(peaks), 2),
            "max_peak_ram_mb": round(max(peaks), 2),
            "total_duration_seconds": round(sum(durations), 2)
        }
