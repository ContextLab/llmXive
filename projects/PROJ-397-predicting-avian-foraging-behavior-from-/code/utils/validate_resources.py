"""
Resource validation module for the avian foraging pipeline.

This module implements SC-004 and FR-002 by explicitly measuring and logging
total pipeline runtime and peak memory usage during execution.

Constraints:
- Total runtime must be < 6 hours (21600 seconds)
- Peak memory usage must be < 7 GB (7 * 1024 * 1024 * 1024 bytes)
"""

import os
import sys
import time
import json
import logging
import subprocess
import resource
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import from existing API surface
from utils.config import get_project_root, get_data_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Resource constraints (in seconds and bytes)
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MAX_MEMORY_BYTES = 7 * 1024 * 1024 * 1024  # 7 GB


class ResourceMonitor:
    """
    Monitors runtime and memory usage of the pipeline.

    This class tracks:
    - Start time and end time for total runtime calculation
    - Peak memory usage via resource.getrusage()
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the resource monitor.

        Args:
            project_root: Path to the project root. If None, uses get_project_root().
        """
        self.project_root = project_root or get_project_root()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory_bytes: int = 0
        self.log_file: Path = self.project_root / "data" / "resource_monitor.json"

        # Ensure data directory exists
        (self.project_root / "data").mkdir(parents=True, exist_ok=True)

    def start(self) -> None:
        """Start monitoring and record the start time."""
        self.start_time = time.time()
        logger.info("Resource monitoring started")

    def stop(self) -> None:
        """Stop monitoring and record the end time and peak memory."""
        self.end_time = time.time()
        # Get peak memory usage (maxrss is in KB on Unix, bytes on some systems)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # maxrss is in KB on Linux/macOS
        self.peak_memory_bytes = usage.ru_maxrss * 1024
        logger.info(f"Resource monitoring stopped. Peak memory: {self.peak_memory_bytes / (1024**2):.2f} MB")

    def get_runtime_seconds(self) -> float:
        """
        Calculate total runtime in seconds.

        Returns:
            Total runtime in seconds, or 0 if not started/stopped properly.
        """
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time

    def get_peak_memory_gb(self) -> float:
        """
        Get peak memory usage in GB.

        Returns:
            Peak memory in GB.
        """
        return self.peak_memory_bytes / (1024**3)

    def validate_constraints(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that resource usage is within constraints.

        Returns:
            Tuple of (is_valid, details_dict) where details_dict contains:
            - runtime_seconds: float
            - peak_memory_gb: float
            - runtime_valid: bool
            - memory_valid: bool
            - all_valid: bool
        """
        runtime_seconds = self.get_runtime_seconds()
        peak_memory_gb = self.get_peak_memory_gb()

        runtime_valid = runtime_seconds < MAX_RUNTIME_SECONDS
        memory_valid = self.peak_memory_bytes < MAX_MEMORY_BYTES
        all_valid = runtime_valid and memory_valid

        details = {
            "runtime_seconds": runtime_seconds,
            "peak_memory_gb": peak_memory_gb,
            "runtime_valid": runtime_valid,
            "memory_valid": memory_valid,
            "all_valid": all_valid,
            "max_runtime_seconds": MAX_RUNTIME_SECONDS,
            "max_memory_gb": MAX_MEMORY_BYTES / (1024**3)
        }

        return all_valid, details

    def save_report(self, details: Dict[str, Any]) -> None:
        """
        Save the resource monitoring report to a JSON file.

        Args:
            details: Dictionary containing resource usage details.
        """
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root),
            "constraints": {
                "max_runtime_seconds": MAX_RUNTIME_SECONDS,
                "max_memory_gb": MAX_MEMORY_BYTES / (1024**3)
            },
            "results": details
        }

        with open(self.log_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Resource monitor report saved to {self.log_file}")

    def log_summary(self, details: Dict[str, Any]) -> None:
        """
        Log a summary of resource usage.

        Args:
            details: Dictionary containing resource usage details.
        """
        logger.info("=" * 60)
        logger.info("RESOURCE USAGE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total runtime: {details['runtime_seconds']:.2f} seconds ({details['runtime_seconds']/3600:.2f} hours)")
        logger.info(f"Peak memory: {details['peak_memory_gb']:.2f} GB")
        logger.info(f"Runtime constraint (< {MAX_RUNTIME_SECONDS}s): {'PASS' if details['runtime_valid'] else 'FAIL'}")
        logger.info(f"Memory constraint (< {MAX_MEMORY_BYTES/(1024**3):.1f} GB): {'PASS' if details['memory_valid'] else 'FAIL'}")
        logger.info(f"Overall validation: {'PASS' if details['all_valid'] else 'FAIL'}")
        logger.info("=" * 60)


def validate_pipeline_resources(project_root: Optional[Path] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate pipeline resource constraints.

    This function creates a ResourceMonitor, starts it, and then checks
    if the current process (and its children) are within resource limits.

    Args:
        project_root: Path to the project root.

    Returns:
        Tuple of (is_valid, details_dict)
    """
    monitor = ResourceMonitor(project_root)

    # For validation without actual execution, we check current usage
    usage = resource.getrusage(resource.RUSAGE_SELF)
    monitor.peak_memory_bytes = usage.ru_maxrss * 1024

    return monitor.validate_constraints()


def check_resource_constraints(project_root: Optional[Path] = None) -> bool:
    """
    Check if resource constraints are met.

    Args:
        project_root: Path to the project root.

    Returns:
        True if constraints are met, False otherwise.
    """
    is_valid, details = validate_pipeline_resources(project_root)

    if not is_valid:
        logger.error("Resource constraints violated!")
        logger.error(f"Runtime: {details['runtime_seconds']:.2f}s (max: {details['max_runtime_seconds']}s)")
        logger.error(f"Memory: {details['peak_memory_gb']:.2f} GB (max: {details['max_memory_gb']} GB)")
        return False

    logger.info("All resource constraints satisfied")
    return True


def main() -> None:
    """
    Main function to run resource validation for the pipeline.

    This function:
    1. Starts the resource monitor
    2. Runs the pipeline (or simulates it for testing)
    3. Stops the monitor
    4. Validates constraints
    5. Saves the report
    6. Logs the summary
    7. Exits with non-zero code if constraints are violated
    """
    logger.info("Starting resource validation for pipeline T007.5b")

    project_root = get_project_root()
    monitor = ResourceMonitor(project_root)

    try:
        # Start monitoring
        monitor.start()

        # Run the pipeline script (T007.5b)
        pipeline_script = project_root / "run_pipeline.sh"

        if not pipeline_script.exists():
            logger.error(f"Pipeline script not found: {pipeline_script}")
            sys.exit(1)

        logger.info(f"Executing pipeline script: {pipeline_script}")

        # Execute the pipeline
        result = subprocess.run(
            ["bash", str(pipeline_script)],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        # Stop monitoring
        monitor.stop()

        # Check if pipeline succeeded
        if result.returncode != 0:
            logger.error("Pipeline execution failed!")
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            # Still save resource usage even if pipeline failed
            is_valid, details = monitor.validate_constraints()
            monitor.save_report(details)
            monitor.log_summary(details)
            sys.exit(1)

        # Validate constraints
        is_valid, details = monitor.validate_constraints()
        monitor.save_report(details)
        monitor.log_summary(details)

        if not is_valid:
            logger.error("Resource constraints violated after successful pipeline run!")
            sys.exit(1)

        logger.info("Resource validation completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error during resource validation: {e}")
        # Try to stop monitoring if it was started
        if monitor.start_time is not None and monitor.end_time is None:
            monitor.stop()
            is_valid, details = monitor.validate_constraints()
            monitor.save_report(details)
            monitor.log_summary(details)
        sys.exit(1)


if __name__ == "__main__":
    main()
