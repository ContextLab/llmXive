"""
Constraint monitoring utilities for T044.
Provides functions to monitor runtime and memory usage during pipeline execution.
"""
import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import psutil


class ConstraintMonitor:
    """
    Monitors computational constraints (runtime and memory) during pipeline execution.
    Designed to work in CI environments to verify SC-004 requirements.
    """

    def __init__(self, max_runtime_seconds: float = 6 * 3600, max_memory_mb: float = 6 * 1024):
        """
        Initialize the constraint monitor.

        Args:
            max_runtime_seconds: Maximum allowed runtime in seconds (default: 6 hours)
            max_memory_mb: Maximum allowed memory in MB (default: 6 GB)
        """
        self.max_runtime_seconds = max_runtime_seconds
        self.max_memory_mb = max_memory_mb
        self.start_time: Optional[float] = None
        self.peak_memory_mb: float = 0.0
        self.monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._results_file: Optional[str] = None

    def _get_current_memory_mb(self) -> float:
        """Get current memory usage of the process in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def _monitor_loop(self, results_file: str, interval: float = 1.0):
        """
        Background loop to monitor memory usage.

        Args:
            results_file: Path to write monitoring results
            interval: Check interval in seconds
        """
        while not self._stop_monitoring.is_set():
            current_memory = self._get_current_memory_mb()
            if current_memory > self.peak_memory_mb:
                self.peak_memory_mb = current_memory

            # Write current state
            with open(results_file, 'w') as f:
                json.dump({
                    'peak_memory_mb': self.peak_memory_mb,
                    'elapsed_seconds': time.time() - self.start_time if self.start_time else 0
                }, f)

            time.sleep(interval)

    def start(self, results_file: str = '/tmp/peak_memory.json'):
        """
        Start monitoring.

        Args:
            results_file: Path to write monitoring results
        """
        self.start_time = time.time()
        self._results_file = results_file
        self.monitoring_thread = threading.Thread(
            target=self._monitor_loop,
            args=(results_file,),
            daemon=True
        )
        self.monitoring_thread.start()

    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return results.

        Returns:
            Dictionary with monitoring results
        """
        self._stop_monitoring.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)

        elapsed_time = time.time() - self.start_time if self.start_time else 0

        return {
            'peak_memory_mb': self.peak_memory_mb,
            'total_runtime_seconds': elapsed_time,
            'max_runtime_seconds': self.max_runtime_seconds,
            'max_memory_mb': self.max_memory_mb
        }

    def check_constraints(self, results: Dict[str, Any]) -> bool:
        """
        Check if results satisfy constraints.

        Args:
            results: Monitoring results dictionary

        Returns:
            True if all constraints are satisfied, False otherwise
        """
        runtime_ok = results['total_runtime_seconds'] <= self.max_runtime_seconds
        memory_ok = results['peak_memory_mb'] <= self.max_memory_mb

        if not runtime_ok:
            print(f"❌ Runtime constraint violated: {results['total_runtime_seconds']:.2f}s > {self.max_runtime_seconds}s")
        if not memory_ok:
            print(f"❌ Memory constraint violated: {results['peak_memory_mb']:.2f}MB > {self.max_memory_mb}MB")

        return runtime_ok and memory_ok

    def save_results(self, results: Dict[str, Any], output_file: str):
        """
        Save results to a JSON file.

        Args:
            results: Results dictionary
            output_file: Output file path
        """
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)


def run_with_constraints(func, max_runtime: float = 6 * 3600, max_memory: float = 6 * 1024):
    """
    Decorator to run a function with constraint monitoring.

    Args:
        func: Function to run
        max_runtime: Maximum allowed runtime in seconds
        max_memory: Maximum allowed memory in MB

    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        monitor = ConstraintMonitor(max_runtime_seconds=max_runtime, max_memory_mb=max_memory)
        results_file = '/tmp/monitoring_results.json'

        try:
            monitor.start(results_file)
            result = func(*args, **kwargs)
            final_results = monitor.stop()
            final_results['success'] = True

            if not monitor.check_constraints(final_results):
                raise RuntimeError("Constraint violation detected")

            return result, final_results
        except Exception as e:
            final_results = monitor.stop()
            final_results['success'] = False
            final_results['error'] = str(e)
            raise
        finally:
            if os.path.exists(results_file):
                os.remove(results_file)

    return wrapper


def main():
    """Main entry point for constraint monitoring script."""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor computational constraints during pipeline execution')
    parser.add_argument('--max-runtime', type=float, default=6 * 3600, help='Maximum runtime in seconds')
    parser.add_argument('--max-memory', type=float, default=6 * 1024, help='Maximum memory in MB')
    parser.add_argument('--output', type=str, default='/tmp/constraint_results.json', help='Output file for results')
    args = parser.parse_args()

    monitor = ConstraintMonitor(
        max_runtime_seconds=args.max_runtime,
        max_memory_mb=args.max_memory
    )

    print(f"Starting constraint monitoring...")
    print(f"Max runtime: {args.max_runtime}s ({args.max_runtime/3600:.1f} hours)")
    print(f"Max memory: {args.max_memory}MB ({args.max_memory/1024:.1f} GB)")

    # In a real scenario, this would wrap the pipeline execution
    # For now, we demonstrate the monitoring capability
    monitor.start('/tmp/peak_memory.json')

    # Simulate some work
    time.sleep(1)

    results = monitor.stop()
    monitor.save_results(results, args.output)

    print(f"Monitoring complete:")
    print(f"  Peak memory: {results['peak_memory_mb']:.2f}MB")
    print(f"  Runtime: {results['total_runtime_seconds']:.2f}s")
    print(f"  Results saved to: {args.output}")


if __name__ == '__main__':
    main()
