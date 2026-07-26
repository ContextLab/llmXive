"""
Runtime enforcer for belief updating model.

Enforces a 6-hour runtime limit and N=30 sample size target.
Provides dynamic sample size reduction logic if constraints are violated.
"""
import os
import sys
import time
import signal
from pathlib import Path
from typing import Dict, Optional, Any, Callable
import json
import logging

from utils.config import get_config
from utils.logger import get_logger
from utils.io import ensure_dir, save_json

# Constants
MAX_RUNTIME_SECONDS = 6 * 60 * 60  # 6 hours
TARGET_SAMPLE_SIZE = 30
MIN_SAMPLE_SIZE = 5
REPORT_PATH = Path("data/models/runtime_enforcement_report.json")

class RuntimeLimitExceeded(Exception):
    """Raised when the runtime limit is exceeded."""
    pass

class SampleSizeReductionRequired(Exception):
    """Raised when sample size must be reduced to meet runtime constraints."""
    def __init__(self, message: str, suggested_size: int):
        super().__init__(message)
        self.suggested_size = suggested_size

class RuntimeEnforcer:
    """
    Enforces runtime and sample size constraints for the belief updating model.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.logger = get_logger(__name__)
        self.start_time: Optional[float] = None
        self.elapsed_time: float = 0.0
        self.max_runtime = self.config.get("modeling", {}).get("max_runtime_seconds", MAX_RUNTIME_SECONDS)
        self.target_sample_size = self.config.get("modeling", {}).get("target_sample_size", TARGET_SAMPLE_SIZE)
        self.min_sample_size = self.config.get("modeling", {}).get("min_sample_size", MIN_SAMPLE_SIZE)
        self.report_data: Dict[str, Any] = {
            "max_runtime_seconds": self.max_runtime,
            "target_sample_size": self.target_sample_size,
            "min_sample_size": self.min_sample_size,
            "enforcement_log": [],
            "final_sample_size": None,
            "runtime_limit_exceeded": False
        }

        # Ensure report directory exists
        ensure_dir(REPORT_PATH.parent)

    def start_timer(self):
        """Start the runtime timer."""
        self.start_time = time.time()
        self.logger.info(f"Runtime timer started. Max runtime: {self.max_runtime} seconds.")
        self._register_signal_handlers()

    def _register_signal_handlers(self):
        """Register signal handlers for graceful timeout."""
        # Only register if not on Windows (signal.SIGALRM not available)
        if sys.platform != "win32":
            signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(int(self.max_runtime))

    def _timeout_handler(self, signum, frame):
        """Handle timeout signal."""
        raise RuntimeLimitExceeded(f"Runtime limit of {self.max_runtime} seconds exceeded.")

    def check_runtime(self) -> bool:
        """
        Check if runtime limit has been exceeded.
        Returns True if within limits, False otherwise.
        """
        if self.start_time is None:
            return True

        current_time = time.time()
        self.elapsed_time = current_time - self.start_time

        if self.elapsed_time > self.max_runtime:
            self.report_data["runtime_limit_exceeded"] = True
            self.report_data["enforcement_log"].append({
                "action": "runtime_limit_exceeded",
                "elapsed_seconds": self.elapsed_time,
                "max_allowed": self.max_runtime
            })
            self.logger.warning(f"Runtime limit exceeded: {self.elapsed_time:.2f}s > {self.max_runtime}s")
            return False

        return True

    def calculate_adaptive_sample_size(self, estimated_time_per_sample: float, current_n: int) -> int:
        """
        Calculate an adaptive sample size to ensure we stay within runtime limits.

        Args:
            estimated_time_per_sample: Estimated time to process one sample (in seconds).
            current_n: Current target sample size.

        Returns:
            Adaptive sample size that should fit within the runtime limit.
        """
        if self.start_time is None:
            self.start_time = time.time()

        remaining_time = self.max_runtime - self.elapsed_time

        if remaining_time <= 0:
            self.logger.warning("No remaining time available. Returning minimum sample size.")
            return self.min_sample_size

        if estimated_time_per_sample <= 0:
            estimated_time_per_sample = 1.0  # Prevent division by zero

        # Calculate how many more samples we can process
        max_additional_samples = int(remaining_time / estimated_time_per_sample)

        # Adjust current_n if it's too high
        if current_n > max_additional_samples + 1:  # +1 for current sample
            new_n = max(self.min_sample_size, max_additional_samples + 1)
            self.report_data["enforcement_log"].append({
                "action": "sample_size_reduced",
                "original_n": current_n,
                "new_n": new_n,
                "estimated_time_per_sample": estimated_time_per_sample,
                "remaining_time": remaining_time
            })
            self.logger.info(f"Reducing sample size from {current_n} to {new_n} to meet runtime constraints.")
            return new_n

        return current_n

    def get_sample_size(self, current_n: int, estimated_time_per_sample: Optional[float] = None) -> int:
        """
        Get the appropriate sample size, adjusting if necessary to meet constraints.

        Args:
            current_n: The requested sample size.
            estimated_time_per_sample: Optional estimate of time per sample.

        Returns:
            The sample size to use (may be reduced if constraints are violated).
        """
        if not self.check_runtime():
            self.logger.error("Runtime limit already exceeded. Cannot process more samples.")
            return 0

        if estimated_time_per_sample is not None:
            return self.calculate_adaptive_sample_size(estimated_time_per_sample, current_n)

        # If no time estimate provided, just return current_n if within limits
        if current_n > self.target_sample_size:
            self.logger.warning(f"Requested sample size {current_n} exceeds target {self.target_sample_size}.")
            return self.target_sample_size

        return current_n

    def finalize(self):
        """Finalize the enforcer and write the report."""
        if self.start_time is not None:
            self.elapsed_time = time.time() - self.start_time

        self.report_data["final_sample_size"] = self.report_data.get("final_sample_size")
        self.report_data["total_runtime_seconds"] = self.elapsed_time
        self.report_data["completed"] = not self.report_data["runtime_limit_exceeded"]

        # Write report
        try:
            save_json(self.report_data, REPORT_PATH)
            self.logger.info(f"Runtime enforcement report written to {REPORT_PATH}")
        except Exception as e:
            self.logger.error(f"Failed to write runtime enforcement report: {e}")

    def __enter__(self):
        self.start_timer()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()
        if sys.platform != "win32":
            signal.alarm(0)  # Cancel the alarm
        return False  # Don't suppress exceptions


def main():
    """
    Main entry point for testing the runtime enforcer.
    """
    logger = get_logger(__name__)
    logger.info("Testing Runtime Enforcer...")

    config = get_config()
    enforcer = RuntimeEnforcer(config)

    # Simulate a process that might exceed limits
    with enforcer:
        sample_size = enforcer.get_sample_size(50)  # Request 50, should be capped at target
        logger.info(f"Adaptive sample size: {sample_size}")

        # Simulate processing
        for i in range(sample_size):
            if not enforcer.check_runtime():
                logger.warning("Runtime limit reached during processing.")
                break
            # Simulate work
            time.sleep(0.1)

    logger.info("Runtime enforcer test completed.")


if __name__ == "__main__":
    main()
