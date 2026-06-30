"""
Runtime monitoring utilities for the Heterogeneous Scientific Foundation Model Benchmark.

Implements SC-002 (Per-task inference ≤ 5 minutes) and SC-003 (Total benchmark ≤ 4 hours).
Records timing metrics to data/runtime_metrics.yaml.
"""
import os
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import threading
from contextlib import contextmanager

from src.utils.logging import get_logger

# Constants
TOTAL_BENCHMARK_LIMIT_SECONDS = 4 * 60 * 60  # 4 hours
PER_TASK_LIMIT_SECONDS = 5 * 60  # 5 minutes
METRICS_OUTPUT_PATH = Path("data/runtime_metrics.yaml")

logger = get_logger(__name__)

class RuntimeMonitor:
    """
    Monitors runtime metrics for benchmark execution.
    Tracks total benchmark time and per-task inference times.
    """

    def __init__(self, output_path: Optional[Path] = None):
        self.output_path = output_path or METRICS_OUTPUT_PATH
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.task_times: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def start_benchmark(self) -> None:
        """Start the total benchmark timer."""
        with self._lock:
            self.start_time = time.time()
            logger.info(f"Benchmark started at {datetime.now(timezone.utc).isoformat()}")

    def stop_benchmark(self) -> None:
        """Stop the total benchmark timer."""
        with self._lock:
            if self.start_time is None:
                raise RuntimeError("Benchmark not started. Call start_benchmark() first.")
            self.end_time = time.time()
            duration = self.end_time - self.start_time
            logger.info(f"Benchmark completed in {duration:.2f} seconds ({duration/3600:.2f} hours)")

    @contextmanager
    def measure_task(self, task_id: str):
        """
        Context manager to measure per-task execution time.
        
        Args:
            task_id: Unique identifier for the task being measured.
        
        Yields:
            None
        
        Example:
            with monitor.measure_task("T001"):
                # Task execution code
                pass
        """
        task_start = time.time()
        try:
            yield
        finally:
            task_end = time.time()
            duration = task_end - task_start
            
            with self._lock:
                if task_id not in self.task_times:
                    self.task_times[task_id] = []
                self.task_times[task_id].append(duration)
            
            logger.info(f"Task {task_id} completed in {duration:.2f} seconds")

    def measure_total_benchmark_time(self) -> Optional[float]:
        """
        Measure and return the total benchmark time in seconds.
        
        Returns:
            Total time in seconds if benchmark has started and stopped, None otherwise.
        """
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time

    def measure_per_task_time(self, task_id: str) -> List[float]:
        """
        Measure and return the list of execution times for a specific task.
        
        Args:
            task_id: The unique identifier of the task.
        
        Returns:
            List of execution times in seconds for the given task.
        """
        with self._lock:
            return self.task_times.get(task_id, [])

    def get_all_task_times(self) -> Dict[str, List[float]]:
        """
        Get all recorded task times.
        
        Returns:
            Dictionary mapping task_id to list of execution times.
        """
        with self._lock:
            return dict(self.task_times)

    def verify_runtime_constraints(self) -> Dict[str, Any]:
        """
        Verify that runtime constraints are met.
        
        Returns:
            Dictionary with verification results for SC-002 and SC-003.
        """
        results = {
            "total_benchmark": {
                "limit_seconds": TOTAL_BENCHMARK_LIMIT_SECONDS,
                "actual_seconds": self.measure_total_benchmark_time(),
                "passed": False,
                "reason": ""
            },
            "per_task": {
                "limit_seconds": PER_TASK_LIMIT_SECONDS,
                "violations": [],
                "passed": True
            }
        }

        # Check total benchmark time
        total_time = self.measure_total_benchmark_time()
        if total_time is not None:
            results["total_benchmark"]["actual_seconds"] = total_time
            if total_time <= TOTAL_BENCHMARK_LIMIT_SECONDS:
                results["total_benchmark"]["passed"] = True
            else:
                results["total_benchmark"]["passed"] = False
                results["total_benchmark"]["reason"] = f"Exceeded limit by {total_time - TOTAL_BENCHMARK_LIMIT_SECONDS:.2f} seconds"

        # Check per-task times
        all_tasks = self.get_all_task_times()
        for task_id, times in all_tasks.items():
            for i, t in enumerate(times):
                if t > PER_TASK_LIMIT_SECONDS:
                    results["per_task"]["passed"] = False
                    results["per_task"]["violations"].append({
                        "task_id": task_id,
                        "attempt": i + 1,
                        "duration_seconds": t,
                        "exceeded_by": t - PER_TASK_LIMIT_SECONDS
                    })

        return results

    def save_metrics(self) -> Path:
        """
        Save runtime metrics to the output YAML file.
        
        Returns:
            Path to the saved metrics file.
        """
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "benchmark": {
                "start_time": datetime.fromtimestamp(self.start_time, timezone.utc).isoformat() if self.start_time else None,
                "end_time": datetime.fromtimestamp(self.end_time, timezone.utc).isoformat() if self.end_time else None,
                "total_duration_seconds": self.measure_total_benchmark_time()
            },
            "task_metrics": {
                task_id: {
                    "count": len(times),
                    "times_seconds": times,
                    "mean_seconds": sum(times) / len(times) if times else 0,
                    "max_seconds": max(times) if times else 0
                }
                for task_id, times in self.get_all_task_times().items()
            },
            "verification": self.verify_runtime_constraints()
        }

        with open(self.output_path, 'w', encoding='utf-8') as f:
            yaml.dump(metrics, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Runtime metrics saved to {self.output_path}")
        return self.output_path

    def reset(self) -> None:
        """Reset the monitor state for a new benchmark run."""
        with self._lock:
            self.start_time = None
            self.end_time = None
            self.task_times = {}


# Global monitor instance
_global_monitor: Optional[RuntimeMonitor] = None

def get_monitor() -> RuntimeMonitor:
    """Get or create the global runtime monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = RuntimeMonitor()
    return _global_monitor

def measure_total_benchmark_time() -> Optional[float]:
    """
    Convenience function to get total benchmark time from global monitor.
    
    Returns:
        Total time in seconds or None if not started.
    """
    return get_monitor().measure_total_benchmark_time()

def measure_per_task_time(task_id: str) -> List[float]:
    """
    Convenience function to get per-task times from global monitor.
    
    Args:
        task_id: The task identifier.
    
    Returns:
        List of execution times for the task.
    """
    return get_monitor().measure_per_task_time(task_id)

def main():
    """
    Main function for standalone testing of the runtime monitor.
    Simulates a benchmark run and verifies constraints.
    """
    import sys
    
    print("Running Runtime Monitor Self-Test...")
    monitor = RuntimeMonitor()
    
    # Simulate benchmark start
    monitor.start_benchmark()
    
    # Simulate some tasks
    task_ids = ["T001", "T002", "T003"]
    for task_id in task_ids:
        with monitor.measure_task(task_id):
            # Simulate work (shorter than 5 mins for test)
            time.sleep(0.1)
    
    # Simulate benchmark end
    monitor.stop_benchmark()
    
    # Verify constraints
    verification = monitor.verify_runtime_constraints()
    print("\nVerification Results:")
    print(f"  Total Benchmark (Limit: 4h): {'PASS' if verification['total_benchmark']['passed'] else 'FAIL'}")
    print(f"  Per-Task (Limit: 5m): {'PASS' if verification['per_task']['passed'] else 'FAIL'}")
    
    if not verification['per_task']['passed']:
        print(f"  Violations: {verification['per_task']['violations']}")
    
    # Save metrics
    output_path = monitor.save_metrics()
    print(f"\nMetrics saved to: {output_path}")
    
    # Print summary
    total_time = monitor.measure_total_benchmark_time()
    print(f"Total time: {total_time:.2f}s")
    print(f"Tasks recorded: {len(monitor.get_all_task_times())}")
    
    return 0 if verification['total_benchmark']['passed'] and verification['per_task']['passed'] else 1

if __name__ == "__main__":
    sys.exit(main())
