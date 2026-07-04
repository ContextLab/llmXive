"""
Timing monitoring utilities for the pipeline execution.

Implements FR-010: Verify pipeline completes within 2-hour CPU budget.
"""
import time
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging

# Constants
PIPELINE_TIME_LIMIT_SECONDS = 2 * 3600  # 2 hours in seconds
TIMING_REPORT_FILENAME = "pipeline_timing_report.json"

logger = logging.getLogger(__name__)


class PipelineTimer:
    """Context manager and utility class for tracking pipeline execution time."""

    def __init__(self, report_dir: str = "data/results"):
        """
        Initialize the pipeline timer.
        
        Args:
            report_dir: Directory to store timing reports.
        """
        self.report_dir = Path(report_dir)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_seconds: float = 0.0
        self.phase_times: Dict[str, float] = {}
        self.current_phase: Optional[str] = None

    def start(self) -> None:
        """Start the overall pipeline timer."""
        self.start_time = time.time()
        self.elapsed_seconds = 0.0
        self.phase_times = {}
        logger.info(f"Pipeline execution started at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    def stop(self) -> None:
        """Stop the overall pipeline timer."""
        if self.start_time is None:
            raise RuntimeError("Timer not started. Call start() first.")
        self.end_time = time.time()
        self.elapsed_seconds = self.end_time - self.start_time
        logger.info(f"Pipeline execution stopped. Total time: {self.elapsed_seconds:.2f}s")

    @contextmanager
    def measure_phase(self, phase_name: str):
        """
        Context manager to measure time spent in a specific phase.
        
        Args:
            phase_name: Name of the pipeline phase.
        
        Usage:
            with timer.measure_phase("data_generation"):
                # do work
        """
        if self.start_time is None:
            self.start()
        
        phase_start = time.time()
        self.current_phase = phase_name
        logger.info(f"Starting phase: {phase_name}")
        
        try:
            yield
        finally:
            phase_end = time.time()
            phase_duration = phase_end - phase_start
            self.phase_times[phase_name] = phase_duration
            logger.info(f"Phase '{phase_name}' completed in {phase_duration:.2f}s")
            self.current_phase = None

    def check_budget(self) -> bool:
        """
        Check if the pipeline execution is within the 2-hour budget.
        
        Returns:
            True if within budget, False otherwise.
        
        Raises:
            RuntimeError: If the timer hasn't been stopped yet.
        """
        if self.end_time is None:
            raise RuntimeError("Cannot check budget before stopping the timer. Call stop() first.")
        
        within_budget = self.elapsed_seconds <= PIPELINE_TIME_LIMIT_SECONDS
        status = "PASS" if within_budget else "FAIL"
        logger.info(f"Time budget check: {status} (elapsed: {self.elapsed_seconds:.2f}s / limit: {PIPELINE_TIME_LIMIT_SECONDS}s)")
        return within_budget

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a timing report dictionary.
        
        Returns:
            Dictionary containing timing information.
        """
        if self.start_time is None or self.end_time is None:
            raise RuntimeError("Cannot generate report before timer is started and stopped.")

        within_budget = self.elapsed_seconds <= PIPELINE_TIME_LIMIT_SECONDS
        
        report = {
            "pipeline_start_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time)),
            "pipeline_end_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.end_time)),
            "total_elapsed_seconds": self.elapsed_seconds,
            "time_limit_seconds": PIPELINE_TIME_LIMIT_SECONDS,
            "within_budget": within_budget,
            "phase_breakdown": self.phase_times,
            "phase_count": len(self.phase_times)
        }
        
        return report

    def save_report(self) -> str:
        """
        Save the timing report to a JSON file.
        
        Returns:
            Path to the saved report file.
        """
        if not self.report_dir.exists():
            self.report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = self.report_dir / TIMING_REPORT_FILENAME
        report_data = self.generate_report()
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Timing report saved to {report_path}")
        return str(report_path)


def verify_pipeline_budget(start_time: float, end_time: float, limit_seconds: int = PIPELINE_TIME_LIMIT_SECONDS) -> bool:
    """
    Verify that pipeline execution time is within the specified budget.
    
    Args:
        start_time: Pipeline start time (Unix timestamp).
        end_time: Pipeline end time (Unix timestamp).
        limit_seconds: Maximum allowed execution time in seconds.
    
    Returns:
        True if within budget, False otherwise.
    """
    elapsed = end_time - start_time
    within_budget = elapsed <= limit_seconds
    
    status = "PASS" if within_budget else "FAIL"
    logger.info(f"Pipeline budget verification: {status} (elapsed: {elapsed:.2f}s / limit: {limit_seconds}s)")
    
    return within_budget


def get_timing_functions():
    """
    Return a dictionary of timing-related functions for external access.
    
    Returns:
        Dictionary mapping function names to callable functions.
    """
    return {
        "PipelineTimer": PipelineTimer,
        "verify_pipeline_budget": verify_pipeline_budget,
        "PIPELINE_TIME_LIMIT_SECONDS": PIPELINE_TIME_LIMIT_SECONDS
    }
