"""
Resource monitoring utility for tracking memory (RSS) and wall-clock time.

Logs current and peak RSS from /proc/self/status and elapsed wall-clock time.
Designed to be invoked during long-running processes to verify streaming compliance.
"""
import os
import time
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure we are in the code directory relative to imports if run as script
# but rely on sys.path for proper module imports in the project structure.

class ResourceMonitor:
    """
    Monitors memory usage (RSS) and wall-clock time for a process.
    
    Reads /proc/self/status for memory stats and uses time.time() for wall-clock.
    """
    
    def __init__(self, start_time: Optional[float] = None):
        """
        Initialize the monitor.
        
        Args:
            start_time: Optional start timestamp. Defaults to current time.
        """
        self.start_time = start_time if start_time is not None else time.time()
        self.peak_rss_kb: int = 0
        self.log_entries: List[Dict[str, Any]] = []
        
        # Initial check
        self._update_metrics()

    def _read_rss_kb(self) -> int:
        """
        Reads the current Resident Set Size (RSS) in kilobytes from /proc/self/status.
        
        Returns:
            RSS in KB. Returns 0 if the file cannot be read (non-Linux systems).
        """
        if os.name != 'posix':
            # Fallback for non-Linux systems (e.g., macOS, Windows) if /proc not available
            # We try to read /proc/self/status first, if it fails, return 0 or raise
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # Format: "VmRSS:     1234 kB"
                            parts = line.split()
                            if len(parts) >= 2:
                                return int(parts[1])
            except (FileNotFoundError, PermissionError, IOError):
                # On non-Linux, /proc might not exist. 
                # For strict compliance with the task "logs /proc/self/status",
                # we assume Linux environment. If not, we log 0 or raise.
                return 0
        else:
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            parts = line.split()
                            if len(parts) >= 2:
                                return int(parts[1])
            except (FileNotFoundError, PermissionError, IOError):
                return 0
        return 0

    def _update_metrics(self) -> Dict[str, Any]:
        """
        Updates internal metrics and returns the current snapshot.
        
        Returns:
            Dictionary with current_rss_kb, elapsed_seconds, timestamp.
        """
        current_rss_kb = self._read_rss_kb()
        if current_rss_kb > self.peak_rss_kb:
            self.peak_rss_kb = current_rss_kb
        
        elapsed = time.time() - self.start_time
        snapshot = {
            "timestamp": time.time(),
            "elapsed_seconds": round(elapsed, 3),
            "current_rss_kb": current_rss_kb,
            "peak_rss_kb": self.peak_rss_kb
        }
        self.log_entries.append(snapshot)
        return snapshot

    def log(self, message: Optional[str] = None) -> Dict[str, Any]:
        """
        Logs the current resource state.
        
        Args:
            message: Optional context message to attach to the log entry.
        
        Returns:
            The snapshot dictionary.
        """
        snapshot = self._update_metrics()
        if message:
            snapshot["message"] = message
        return snapshot

    def get_report(self) -> Dict[str, Any]:
        """
        Generates a summary report of the monitoring session.
        
        Returns:
            Dictionary with summary statistics.
        """
        if not self.log_entries:
            self._update_metrics()
        
        return {
            "start_time": self.start_time,
            "end_time": time.time(),
            "total_elapsed_seconds": round(time.time() - self.start_time, 3),
            "peak_rss_kb": self.peak_rss_kb,
            "peak_rss_mb": round(self.peak_rss_kb / 1024, 2),
            "sample_count": len(self.log_entries),
            "log_entries": self.log_entries
        }

    def save_report(self, output_path: str) -> None:
        """
        Saves the monitoring report to a JSON file.
        
        Args:
            output_path: Path to the output JSON file.
        """
        report = self.get_report()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)


def main():
    """
    CLI entry point for resource monitoring.
    
    Usage:
        python -m src.utils.resource_monitor [output_path]
        
    If no output path is provided, defaults to 'data/results/extraction_memory_log.json'.
    This script runs a dummy loop to demonstrate monitoring, or can be imported
    to monitor other processes.
    """
    output_path = sys.argv[1] if len(sys.argv) > 1 else "data/results/extraction_memory_log.json"
    
    print(f"Starting resource monitor. Output will be saved to: {output_path}")
    
    monitor = ResourceMonitor()
    
    # Simulate a workload for demonstration if run directly
    # In real usage, this class is instantiated around the code being monitored.
    # We perform a dummy loop to generate some logs.
    print("Running dummy workload to generate logs...")
    for i in range(5):
        # Simulate some work
        _ = sum(range(1000000))
        log_entry = monitor.log(message=f"Work iteration {i+1}")
        print(f"  Iteration {i+1}: RSS={log_entry['current_rss_kb']} KB, Peak={log_entry['peak_rss_kb']} KB")
        time.sleep(0.1)
    
    monitor.save_report(output_path)
    print(f"Monitoring complete. Peak RSS: {monitor.peak_rss_kb} KB ({monitor.peak_rss_kb/1024:.2f} MB)")
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()