"""
CPU-time profiling module for simulation steps.

Measures per-step execution time to validate SC-002 (<=60 min runtime).
Outputs profiling data to data/analysis/profiler_report.json.
"""
import json
import time
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

from code.src.utils.config import load_config

logger = logging.getLogger(__name__)


class SimulationProfiler:
    """
    Profiles CPU time spent on spin-flip iterations.

    Attributes:
        start_time (float): Timestamp when profiling started.
        step_times (List[float]): List of durations for each step.
        total_steps (int): Total number of steps executed.
        config (Dict[str, Any]): Loaded configuration.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the profiler.

        Args:
            config_path: Path to config.yaml. If None, uses default location.
        """
        self.config = load_config(config_path)
        self.start_time: Optional[float] = None
        self.step_times: List[float] = []
        self.total_steps: int = 0
        self.timeout_seconds: float = self.config.get('simulation_params', {}).get('timeout_seconds', 3600)

    def start(self):
        """Start the profiler timer."""
        self.start_time = time.perf_counter()
        self.step_times = []
        self.total_steps = 0
        logger.info("Profiler started.")

    def record_step(self, duration: float):
        """
        Record the duration of a single spin-flip iteration.

        Args:
            duration: Time taken for the step in seconds.
        """
        self.step_times.append(duration)
        self.total_steps += 1

    def stop(self) -> Dict[str, Any]:
        """
        Stop the profiler and compute summary statistics.

        Returns:
            Dictionary containing profiling metrics.
        """
        if self.start_time is None:
            raise RuntimeError("Profiler was not started.")

        total_duration = time.perf_counter() - self.start_time

        stats = {
            "total_steps": self.total_steps,
            "total_duration_seconds": total_duration,
            "timeout_seconds": self.timeout_seconds,
            "within_timeout": total_duration <= self.timeout_seconds,
            "time_per_step_stats": {
                "mean": float(np.mean(self.step_times)) if self.step_times else 0.0,
                "std": float(np.std(self.step_times)) if self.step_times else 0.0,
                "min": float(np.min(self.step_times)) if self.step_times else 0.0,
                "max": float(np.max(self.step_times)) if self.step_times else 0.0,
                "median": float(np.median(self.step_times)) if self.step_times else 0.0,
            },
            "per_step_times": self.step_times,
        }

        logger.info(
            f"Profiler stopped. Total steps: {self.total_steps}, "
            f"Total duration: {total_duration:.4f}s, "
            f"Mean time/step: {stats['time_per_step_stats']['mean']:.6f}s"
        )

        return stats

    def save_report(self, output_path: Optional[str] = None, metrics: Optional[Dict[str, Any]] = None):
        """
        Save the profiling report to a JSON file.

        Args:
            output_path: Path to save the report. Defaults to data/analysis/profiler_report.json.
            metrics: Pre-computed metrics dictionary. If None, calls stop() to compute them.
        """
        if metrics is None:
            metrics = self.stop()

        if output_path is None:
            output_path = "data/analysis/profiler_report.json"

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Profiler report saved to {output_file}")
        return output_file


def profile_spin_flip_iteration(func):
    """
    Decorator to profile a function representing a spin-flip iteration.

    Args:
        func: The function to profile.

    Returns:
        Wrapped function that records execution time.
    """
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start

        # If a profiler instance is passed in kwargs or args, record it.
        # We assume the first argument or 'profiler' kwarg is the profiler.
        profiler = kwargs.get('profiler')
        if profiler is None and args:
            # Check if first arg is a profiler (heuristic: has record_step method)
            if hasattr(args[0], 'record_step'):
                profiler = args[0]

        if profiler and hasattr(profiler, 'record_step'):
            profiler.record_step(duration)

        return result
    return wrapper


def run_profiler_demo():
    """
    Demonstrate the profiler by simulating a few steps.
    This is for testing the profiling logic, not the actual simulation.
    """
    logger.info("Running profiler demo...")

    profiler = SimulationProfiler()
    profiler.start()

    # Simulate some steps with varying durations
    for i in range(10):
        # Simulate work
        time.sleep(0.01 * (i + 1))
        profiler.record_step(0.01 * (i + 1))

    metrics = profiler.stop()
    profiler.save_report(metrics=metrics)

    logger.info("Profiler demo completed.")
    return metrics


def main():
    """
    Main entry point for the profiler module.
    Can be run directly to generate a demo report or integrated into simulation.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_profiler_demo()


if __name__ == "__main__":
    main()