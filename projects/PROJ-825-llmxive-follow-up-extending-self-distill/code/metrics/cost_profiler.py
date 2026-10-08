"""
Cost Profiler for tracking CPU time and RSS memory per step.

Implements T010 requirements.
"""
import os
import resource
import time
import json
from pathlib import Path
from typing import Dict, Optional, List

class CostProfiler:
    """
    Tracks CPU time and Resident Set Size (RSS) memory usage.
    """
    
    def __init__(self, output_path: Optional[str] = None):
        self.output_path = output_path
        self.start_time: Optional[float] = None
        self.start_cpu: Optional[float] = None
        self.peak_rss: float = 0.0
        self.step_metrics: List[Dict] = []
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the profiler."""
        self.start_time = time.time()
        self.start_cpu = time.process_time()
        self._update_peak_rss()

    def _update_peak_rss(self):
        """Update the peak RSS memory usage."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        current_rss = usage.ru_maxrss / (1024 * 1024) # Convert KB to GB
        if current_rss > self.peak_rss:
            self.peak_rss = current_rss

    def step(self, step_id: int, extra_metrics: Optional[Dict] = None):
        """
        Record metrics for a single step.
        
        Args:
            step_id: The current step number.
            extra_metrics: Additional metrics to log (e.g., loss, reward).
        """
        self._update_peak_rss()
        
        current_time = time.time()
        current_cpu = time.process_time()
        
        elapsed_time = current_time - self.start_time if self.start_time else 0.0
        elapsed_cpu = current_cpu - self.start_cpu if self.start_cpu else 0.0
        
        metrics = {
            "step_id": step_id,
            "elapsed_time_sec": elapsed_time,
            "elapsed_cpu_sec": elapsed_cpu,
            "current_rss_gb": self.peak_rss,
            "peak_rss_gb": self.peak_rss
        }
        
        if extra_metrics:
            metrics.update(extra_metrics)
        
        self.step_metrics.append(metrics)
        return metrics

    def stop(self):
        """Stop the profiler and optionally save results."""
        self._update_peak_rss()
        if self.output_path:
            self.save()

    def save(self):
        """Save the collected metrics to a JSON file."""
        if not self.output_path:
            return
        
        final_metrics = {
            "total_steps": len(self.step_metrics),
            "peak_rss_gb": self.peak_rss,
            "steps": self.step_metrics
        }
        
        with open(self.output_path, 'w') as f:
            json.dump(final_metrics, f, indent=2)

    def get_summary(self) -> Dict:
        """Get a summary of the profiling run."""
        return {
            "total_steps": len(self.step_metrics),
            "peak_rss_gb": self.peak_rss,
            "avg_cpu_per_step": (self.step_metrics[-1]["elapsed_cpu_sec"] / len(self.step_metrics)) if self.step_metrics else 0
        }
