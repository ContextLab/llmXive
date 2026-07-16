"""
Timing utilities for pipeline execution monitoring.

This module provides classes and functions to measure pipeline execution time,
verify against budget constraints, and generate timing reports.
"""
import time
import resource
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class TimingReport:
    """Data class to hold timing information for a pipeline execution."""
    
    def __init__(
        self,
        total_time_seconds: float,
        budget_seconds: float,
        stages: list,
        status: str,
        error: Optional[str] = None,
        cpu_time_seconds: Optional[float] = None,
        memory_peak_mb: Optional[float] = None
    ):
        self.total_time_seconds = total_time_seconds
        self.budget_seconds = budget_seconds
        self.stages = stages
        self.status = status
        self.error = error
        self.cpu_time_seconds = cpu_time_seconds
        self.memory_peak_mb = memory_peak_mb
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert timing report to dictionary for JSON serialization."""
        return {
            "total_time_seconds": self.total_time_seconds,
            "budget_seconds": self.budget_seconds,
            "stages": self.stages,
            "status": self.status,
            "error": self.error,
            "cpu_time_seconds": self.cpu_time_seconds,
            "memory_peak_mb": self.memory_peak_mb
        }
    
    def __repr__(self):
        return f"TimingReport(status={self.status}, time={self.total_time_seconds:.2f}s)"

@contextmanager
def timed_pipeline(stage_name: str, report_list: list):
    """
    Context manager to time a pipeline stage and record the duration.
    
    Args:
        stage_name: Name of the pipeline stage
        report_list: List to append timing results to
        
    Yields:
        None
    """
    start_time = time.time()
    start_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime
    
    try:
        yield
    finally:
        end_time = time.time()
        end_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        
        duration = end_time - start_time
        cpu_duration = end_cpu - start_cpu
        
        stage_timing = {
            "name": stage_name,
            "duration_seconds": duration,
            "cpu_seconds": cpu_duration
        }
        
        report_list.append(stage_timing)
        logger.info(f"Stage '{stage_name}' completed in {duration:.2f}s (CPU: {cpu_duration:.2f}s)")

def check_budget_usage(
    elapsed_time: float,
    budget_seconds: float,
    threshold_percent: float = 80.0
) -> Dict[str, Any]:
    """
    Check current time usage against budget and return status.
    
    Args:
        elapsed_time: Time elapsed in seconds
        budget_seconds: Total budget in seconds
        threshold_percent: Percentage at which to warn (default 80%)
        
    Returns:
        Dict with status information
    """
    usage_percent = (elapsed_time / budget_seconds) * 100
    
    result = {
        "elapsed_seconds": elapsed_time,
        "budget_seconds": budget_seconds,
        "usage_percent": usage_percent,
        "remaining_seconds": budget_seconds - elapsed_time,
        "status": "ok"
    }
    
    if usage_percent >= 100:
        result["status"] = "exceeded"
        logger.warning(f"Pipeline budget EXCEEDED: {usage_percent:.1f}% used")
    elif usage_percent >= threshold_percent:
        result["status"] = "warning"
        logger.warning(f"Pipeline budget WARNING: {usage_percent:.1f}% used")
    else:
        result["status"] = "ok"
        logger.info(f"Pipeline budget OK: {usage_percent:.1f}% used")
    
    return result

def write_timing_report(timing_report: TimingReport, output_path: Path):
    """
    Write timing report to JSON file.
    
    Args:
        timing_report: TimingReport object to serialize
        output_path: Path to write the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(timing_report.to_dict(), f, indent=2)
    
    logger.info(f"Timing report written to {output_path}")

def verify_pipeline_budget(timing_report: TimingReport) -> bool:
    """
    Verify that pipeline execution stayed within budget.
    
    Args:
        timing_report: TimingReport object with execution metrics
        
    Returns:
        True if within budget, False otherwise
    """
    if timing_report.total_time_seconds > timing_report.budget_seconds:
        logger.error(
            f"Pipeline exceeded budget: {timing_report.total_time_seconds:.2f}s "
            f"vs {timing_report.budget_seconds:.2f}s budget"
        )
        return False
    
    logger.info(
        f"Pipeline within budget: {timing_report.total_time_seconds:.2f}s "
        f"vs {timing_report.budget_seconds:.2f}s budget"
    )
    return True

def get_timing_functions():
    """
    Get dictionary of available timing functions.
    
    Returns:
        Dict mapping function names to callable functions
    """
    return {
        "timed_pipeline": timed_pipeline,
        "check_budget_usage": check_budget_usage,
        "write_timing_report": write_timing_report,
        "verify_pipeline_budget": verify_pipeline_budget
    }
