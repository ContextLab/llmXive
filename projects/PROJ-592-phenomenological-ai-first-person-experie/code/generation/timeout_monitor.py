"""Timeout monitoring and sample size enforcement."""
from __future__ import annotations

import json
import logging
import signal
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

logger = get_logger(__name__)


class GenerationTimeoutError(Exception):
    """Raised when a generation task exceeds the timeout limit."""
    pass


@dataclass
class SampleCounter:
    """Tracks successful and failed samples."""
    successful: int = 0
    failed: int = 0
    total_attempts: int = 0
    timestamps: List[str] = field(default_factory=list)

    def record_success(self) -> None:
        self.successful += 1
        self.total_attempts += 1
        self.timestamps.append(datetime.utcnow().isoformat())

    def record_failure(self) -> None:
        self.failed += 1
        self.total_attempts += 1

    def get_stats(self) -> Dict[str, Any]:
        return {
            "successful": self.successful,
            "failed": self.failed,
            "total_attempts": self.total_attempts,
            "success_rate": self.successful / self.total_attempts if self.total_attempts > 0 else 0.0,
        }


@dataclass
class TimeoutContext:
    """Context manager for enforcing timeouts on generation tasks."""

    def __init__(self, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds
        self.timer: Optional[threading.Timer] = None
        self.timed_out = False

    def _timeout_handler(self) -> None:
        self.timed_out = True
        raise GenerationTimeoutError(f"Operation exceeded {self.timeout_seconds}s timeout")

    def __enter__(self) -> "TimeoutContext":
        self.timer = threading.Timer(self.timeout_seconds, self._timeout_handler)
        self.timer.daemon = True
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.timer:
            self.timer.cancel()
        return False


def run_with_timeout(
    func: Callable,
    timeout_seconds: int = 60,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Run a function with a timeout, raising GenerationTimeoutError if exceeded."""
    with TimeoutContext(timeout_seconds):
        return func(*args, **kwargs)


def log_sample_status(
    counter: SampleCounter,
    strategy: str,
    prompt_id: str,
    success: bool,
) -> None:
    """Log the status of a sample generation attempt."""
    status = "SUCCESS" if success else "FAILURE"
    logger.info(f"Sample [{strategy}:{prompt_id}] {status} - Stats: {counter.get_stats()}")


def save_summary(counter: SampleCounter, output_path: str) -> None:
    """Save the sample generation summary to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "stats": counter.get_stats(),
    }
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary saved to {output_path}")


def enforce_minimum_samples(
    counter: SampleCounter,
    minimum: int = 80,
    raise_on_failure: bool = True,
) -> bool:
    """Check if the minimum number of successful samples has been reached."""
    if counter.successful >= minimum:
        logger.info(f"Minimum sample requirement met: {counter.successful}/{minimum}")
        return True
    else:
        msg = f"Minimum sample requirement NOT met: {counter.successful}/{minimum}"
        logger.warning(msg)
        if raise_on_failure:
            raise RuntimeError(msg)
        return False


def main() -> None:
    """Entry point for timeout monitor (for testing)."""
    counter = SampleCounter()
    counter.record_success()
    counter.record_success()
    counter.record_failure()
    print(f"Stats: {counter.get_stats()}")


if __name__ == "__main__":
    main()
