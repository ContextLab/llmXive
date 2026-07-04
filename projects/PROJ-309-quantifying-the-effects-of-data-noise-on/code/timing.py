"""
Timing utilities for pipeline execution monitoring.

Implements FR-010: Verify pipeline completes within 2-hour CPU budget.
"""
import time
import resource
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path
import json

# Constants
CPU_BUDGET_SECONDS = 2 * 60 * 60  # 2 hours in seconds
WARNING_THRESHOLD = 0.8  # Warn if 80% of budget is used
CRITICAL_THRESHOLD = 0.95  # Critical if 95% of budget is used

logger = logging.getLogger(__name__)


class TimingReport:
    """Container for timing and resource usage statistics."""

    def __init__(
        self,
        wall_time: float,
        cpu_time: float,
        peak_memory_mb: float,
        budget_seconds: float,
        budget_exceeded: bool,
        warning_level: str = "none"
    ):
        self.wall_time = wall_time
        self.cpu_time = cpu_time
        self.peak_memory_mb = peak_memory_mb
        self.budget_seconds = budget_seconds
        self.budget_exceeded = budget_exceeded
        self.warning_level = warning_level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wall_time_seconds": round(self.wall_time, 3),
            "cpu_time_seconds": round(self.cpu_time, 3),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "cpu_budget_seconds": self.budget_seconds,
            "budget_remaining_seconds": round(self.budget_seconds - self.cpu_time, 3),
            "budget_exceeded": self.budget_exceeded,
            "warning_level": self.warning_level,
            "budget_utilization_percent": round((self.cpu_time / self.budget_seconds) * 100, 2)
        }

    def __repr__(self) -> str:
        status = "EXCEEDED" if self.budget_exceeded else "OK"
        return (
            f"TimingReport(wall={self.wall_time:.1f}s, cpu={self.cpu_time:.1f}s, "
            f"mem={self.peak_memory_mb:.1f}MB, status={status})"
        )


@contextmanager
def timed_pipeline(phase_name: str = "pipeline"):
    """
    Context manager to time a pipeline phase and log results.

    Args:
        phase_name: Name of the phase being timed for logging.

    Yields:
        None. Usage is for timing the block.
    """
    start_wall = time.time()
    start_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime

    try:
        yield
    finally:
        end_wall = time.time()
        end_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime

        wall_elapsed = end_wall - start_wall
        cpu_elapsed = end_cpu - start_cpu
        # Peak memory in MB (ru_maxrss is in KB on Linux, bytes on macOS)
        # ru_maxrss is typically KB on Linux
        peak_mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_mem_mb = peak_mem_kb / 1024.0

        budget_used = cpu_elapsed / CPU_BUDGET_SECONDS

        if budget_used > CRITICAL_THRESHOLD:
            warning_level = "CRITICAL"
            logger.critical(
                f"[{phase_name}] CPU usage critical: {cpu_elapsed:.1f}s "
                f"({budget_used*100:.1f}% of budget)"
            )
        elif budget_used > WARNING_THRESHOLD:
            warning_level = "WARNING"
            logger.warning(
                f"[{phase_name}] CPU usage high: {cpu_elapsed:.1f}s "
                f"({budget_used*100:.1f}% of budget)"
            )
        else:
            warning_level = "none"

        logger.info(
            f"[{phase_name}] Completed in {wall_elapsed:.2f}s wall time, "
            f"{cpu_elapsed:.2f}s CPU time. Peak mem: {peak_mem_mb:.1f}MB."
        )

        yield TimingReport(
            wall_time=wall_elapsed,
            cpu_time=cpu_elapsed,
            peak_memory_mb=peak_mem_mb,
            budget_seconds=CPU_BUDGET_SECONDS,
            budget_exceeded=cpu_elapsed > CPU_BUDGET_SECONDS,
            warning_level=warning_level
        )


def check_budget_usage(report: Optional[TimingReport] = None) -> bool:
    """
    Check if the pipeline has exceeded the CPU budget.

    Args:
        report: A TimingReport instance. If None, checks current usage.

    Returns:
        True if budget is NOT exceeded (success), False otherwise.
    """
    if report is None:
        # Current usage check
        current_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        exceeded = current_cpu > CPU_BUDGET_SECONDS
        if exceeded:
            logger.error(f"CPU budget exceeded: {current_cpu:.1f}s > {CPU_BUDGET_SECONDS}s")
        return not exceeded

    if report.budget_exceeded:
        logger.error(
            f"Pipeline exceeded CPU budget: {report.cpu_time:.1f}s > "
            f"{report.budget_seconds}s"
        )
        return False

    return True


def write_timing_report(report: TimingReport, output_path: Path) -> None:
    """
    Write the timing report to a JSON file.

    Args:
        report: The TimingReport instance.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    logger.info(f"Timing report written to {output_path}")


def verify_pipeline_budget() -> bool:
    """
    Verifies that the current CPU usage is within the 2-hour budget.
    Used as a final check after pipeline execution.

    Returns:
        True if within budget, False otherwise.
    """
    current_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime
    if current_cpu > CPU_BUDGET_SECONDS:
        logger.error(
            f"Pipeline verification failed: CPU time {current_cpu:.1f}s "
            f"exceeds budget {CPU_BUDGET_SECONDS}s"
        )
        return False
    logger.info(
        f"Pipeline verification passed: CPU time {current_cpu:.1f}s "
        f"within budget {CPU_BUDGET_SECONDS}s"
    )
    return True
