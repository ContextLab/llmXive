"""
CPU utilization monitoring module for llmXive research pipeline.

Implements real-time CPU monitoring using psutil to log cpu_percent
for every execution step, synchronized with the logging frequency of T005a.
"""

import os
import time
import json
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class CPUMonitor:
    """
    Monitors CPU utilization during experiment execution.
    
    Logs cpu_percent at the same frequency as the base logging infrastructure (T005a).
    Output is written to data/processed/experiment.log in JSON format.
    """
    
    def __init__(
        self,
        log_path: Optional[str] = None,
        sample_interval: float = 0.1
    ):
        """
        Initialize the CPU monitor.
        
        Args:
            log_path: Path to the log file. Defaults to data/processed/experiment.log
            sample_interval: Interval in seconds between CPU samples.
        """
        if log_path is None:
            log_path = "data/processed/experiment.log"
        
        self.log_path = Path(log_path)
        self.sample_interval = sample_interval
        self._process = psutil.Process(os.getpid())
        self._last_sample_time: Optional[float] = None
        self._cpu_percent_history: List[Dict[str, Any]] = []
        
        # Ensure log directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clear existing log file to start fresh
        self.log_path.write_text("")
    
    def start(self) -> None:
        """Start monitoring (initializes psutil process)."""
        # psutil.Process() already initialized in __init__
        # This method can be used for any additional start-up logic
        pass
    
    def sample(self) -> Dict[str, Any]:
        """
        Take a single CPU utilization sample.
        
        Returns:
            Dictionary containing timestamp, cpu_percent, and process info.
        """
        timestamp = datetime.utcnow().isoformat()
        cpu_percent = self._process.cpu_percent(interval=None)
        
        sample = {
            "timestamp": timestamp,
            "cpu_percent": cpu_percent,
            "process_id": self._process.pid,
            "process_name": self._process.name(),
            "sample_interval": self.sample_interval
        }
        
        self._cpu_percent_history.append(sample)
        self._last_sample_time = time.time()
        
        return sample
    
    def log_sample(self, sample: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a CPU sample to the experiment log file.
        
        Args:
            sample: Pre-computed sample dictionary. If None, a new sample is taken.
        """
        if sample is None:
            sample = self.sample()
        
        log_entry = {
            "type": "cpu_monitor",
            "data": sample
        }
        
        # Append to log file as JSON Lines
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def log_step(self, step_name: str, extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log CPU utilization for a specific execution step.
        
        This is the primary method for logging at the same frequency as T005a.
        
        Args:
            step_name: Name of the execution step being monitored.
            extra_data: Optional additional data to include in the log entry.
        
        Returns:
            The logged sample dictionary.
        """
        sample = self.sample()
        sample["step_name"] = step_name
        
        if extra_data:
            sample.update(extra_data)
        
        log_entry = {
            "type": "cpu_monitor_step",
            "timestamp": datetime.utcnow().isoformat(),
            "step_name": step_name,
            "cpu_percent": sample["cpu_percent"],
            "process_id": self._process.pid,
            "extra_data": extra_data or {}
        }
        
        # Append to log file
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        return sample
    
    def get_average_cpu(self) -> float:
        """
        Calculate the average CPU utilization across all samples.
        
        Returns:
            Average CPU percentage, or 0.0 if no samples exist.
        """
        if not self._cpu_percent_history:
            return 0.0
        
        total = sum(s["cpu_percent"] for s in self._cpu_percent_history)
        return total / len(self._cpu_percent_history)
    
    def get_max_cpu(self) -> float:
        """
        Get the maximum CPU utilization observed.
        
        Returns:
            Maximum CPU percentage, or 0.0 if no samples exist.
        """
        if not self._cpu_percent_history:
            return 0.0
        
        return max(s["cpu_percent"] for s in self._cpu_percent_history)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the monitoring session.
        
        Returns:
            Dictionary with average, max, min, and sample count.
        """
        if not self._cpu_percent_history:
            return {
                "sample_count": 0,
                "average_cpu": 0.0,
                "max_cpu": 0.0,
                "min_cpu": 0.0,
                "total_duration_seconds": 0.0
            }
        
        values = [s["cpu_percent"] for s in self._cpu_percent_history]
        return {
            "sample_count": len(values),
            "average_cpu": sum(values) / len(values),
            "max_cpu": max(values),
            "min_cpu": min(values),
            "total_duration_seconds": time.time() - (self._last_sample_time or time.time())
        }

# Convenience function for quick monitoring
def monitor_cpu_for_step(step_name: str, log_path: str = "data/processed/experiment.log") -> Dict[str, Any]:
    """
    Convenience function to monitor CPU for a single step.
    
    Args:
        step_name: Name of the step to monitor.
        log_path: Path to the log file.
    
    Returns:
        The logged sample dictionary.
    """
    monitor = CPUMonitor(log_path=log_path)
    return monitor.log_step(step_name)

def main():
    """
    Command-line interface for testing CPU monitoring.
    
    Runs a simple loop to demonstrate CPU logging.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test CPU monitoring")
    parser.add_argument(
        "--steps",
        type=int,
        default=5,
        help="Number of steps to monitor"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Interval between samples in seconds"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/experiment.log",
        help="Output log file path"
    )
    
    args = parser.parse_args()
    
    monitor = CPUMonitor(log_path=args.output, sample_interval=args.interval)
    
    print(f"Starting CPU monitoring for {args.steps} steps...")
    print(f"Log file: {args.output}")
    
    for i in range(args.steps):
        step_name = f"test_step_{i}"
        sample = monitor.log_step(step_name)
        print(f"  {step_name}: {sample['cpu_percent']:.1f}%")
        time.sleep(args.interval)
    
    stats = monitor.get_stats()
    print(f"\nMonitoring complete.")
    print(f"  Samples: {stats['sample_count']}")
    print(f"  Average CPU: {stats['average_cpu']:.1f}%")
    print(f"  Max CPU: {stats['max_cpu']:.1f}%")
    print(f"  Min CPU: {stats['min_cpu']:.1f}%")

if __name__ == "__main__":
    main()