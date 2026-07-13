"""
Timeout handling and sample-size logging for the generation pipeline.

This module provides:
1. A context manager for enforcing generation timeouts.
2. A logging utility to track successful sample counts per condition.
3. Integration with the runner to ensure >= 80 samples per condition.
"""
from __future__ import annotations

import json
import logging
import signal
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from utils.logging import get_logger, log_operation


class GenerationTimeoutError(Exception):
    """Raised when a generation step exceeds the allowed time limit."""
    pass


@dataclass
class SampleCounter:
    """Tracks successful generation counts per condition."""
    counts: Dict[str, int] = field(default_factory=dict)
    log_path: Path = field(default_factory=lambda: Path("data/processed/sample_counts.json"))
    
    def increment(self, condition: str) -> int:
        """Increment the count for a condition and return the new total."""
        current = self.counts.get(condition, 0)
        self.counts[condition] = current + 1
        self._save()
        return self.counts[condition]
    
    def get(self, condition: str) -> int:
        """Get current count for a condition."""
        return self.counts.get(condition, 0)
    
    def check_minimum(self, condition: str, minimum: int = 80) -> bool:
        """Check if a condition meets the minimum sample requirement."""
        return self.get(condition) >= minimum
    
    def _save(self) -> None:
        """Persist counts to disk."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.counts, f, indent=2, default=str)
    
    def load(self) -> None:
        """Load counts from disk if available."""
        if self.log_path.exists():
            with open(self.log_path, "r", encoding="utf-8") as f:
                self.counts = json.load(f)


class TimeoutContext:
    """Context manager for enforcing a timeout on a block of code."""
    
    def __init__(self, seconds: int, logger: Optional[Any] = None):
        self.seconds = seconds
        self.logger = logger or get_logger()
        self._original_handler = None
        self._timer: Optional[threading.Timer] = None

    def _timeout_handler(self, signum, frame):
        raise GenerationTimeoutError(f"Generation exceeded {self.seconds} seconds")

    def _thread_timeout(self):
        time.sleep(self.seconds)
        raise GenerationTimeoutError(f"Generation exceeded {self.seconds} seconds (thread)")

    def __enter__(self):
        # Use threading timer for cross-platform compatibility (Windows doesn't support signal.alarm)
        self._timer = threading.Timer(self.seconds, self._thread_timeout)
        self._timer.daemon = True
        self._timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._timer:
            self._timer.cancel()
            self._timer = None
        # Do not suppress exceptions
        return False


def run_with_timeout(func: Callable, timeout_seconds: int = 60) -> Callable:
    """Decorator to enforce a timeout on a function."""
    def wrapper(*args, **kwargs):
        with TimeoutContext(timeout_seconds):
            return func(*args, **kwargs)
    return wrapper


def log_sample_status(
    condition: str,
    success: bool,
    sample_id: str,
    counter: SampleCounter,
    logger: Optional[Any] = None
) -> None:
    """Log a sample generation event and update counters."""
    log = logger or get_logger()
    if success:
        new_count = counter.increment(condition)
        log_operation(
            "sample_generated",
            condition=condition,
            sample_id=sample_id,
            current_count=new_count,
            status="success"
        )
    else:
        log_operation(
            "sample_failed",
            condition=condition,
            sample_id=sample_id,
            status="failure"
        )


def enforce_minimum_samples(
    counter: SampleCounter,
    minimum: int = 80,
    logger: Optional[Any] = None
) -> Tuple[bool, Dict[str, int]]:
    """
    Check if all tracked conditions meet the minimum sample requirement.
    
    Returns:
        Tuple of (all_satisfied, counts_dict)
    """
    log = logger or get_logger()
    all_satisfied = True
    counts = counter.counts.copy()
    
    for condition, count in counts.items():
        if count < minimum:
            all_satisfied = False
            log_operation(
                "minimum_not_met",
                condition=condition,
                current_count=count,
                required_minimum=minimum,
                status="warning"
            )
    
    if all_satisfied:
        log_operation(
            "minimum_satisfied",
            all_conditions_met=True,
            status="info"
        )
    
    return all_satisfied, counts


def main() -> None:
    """CLI entry point for testing the timeout and logging utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test timeout and sample logging")
    parser.add_argument("--test-timeout", action="store_true", help="Test timeout functionality")
    parser.add_argument("--test-logging", action="store_true", help="Test logging functionality")
    parser.add_argument("--condition", type=str, default="test", help="Condition name for testing")
    
    args = parser.parse_args()
    
    logger = get_logger()
    counter = SampleCounter()
    counter.load()
    
    if args.test_timeout:
        logger.log("test_timeout", message="Starting timeout test")
        try:
            with TimeoutContext(2, logger):
                logger.log("sleeping", message="Sleeping for 3 seconds...")
                time.sleep(3)
        except GenerationTimeoutError as e:
            logger.log("timeout_caught", message=str(e))
            print(f"Timeout correctly caught: {e}")
        
    if args.test_logging:
        logger.log("test_logging", message="Starting logging test")
        for i in range(5):
            log_sample_status(args.condition, True, f"sample_{i}", counter, logger)
        
        satisfied, counts = enforce_minimum_samples(counter, minimum=3, logger=logger)
        print(f"Counts: {counts}")
        print(f"Minimum (3) satisfied: {satisfied}")
        
        # Test minimum check
        satisfied_80, _ = enforce_minimum_samples(counter, minimum=80, logger=logger)
        print(f"Minimum (80) satisfied: {satisfied_80}")

if __name__ == "__main__":
    main()
