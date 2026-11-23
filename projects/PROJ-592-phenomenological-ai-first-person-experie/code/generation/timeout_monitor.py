"""
Timeout handling and sample-size logging for the generation pipeline.
Implements timeout per generation and logs sample counts to data/raw/generation_log.json.
"""
from __future__ import annotations

import json
import logging
import signal
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from code.utils.logging import get_logger, log_operation

logger = get_logger(__name__)


class GenerationTimeoutError(Exception):
    """Raised when a generation attempt exceeds the timeout limit."""
    pass


class SampleCounter:
    """Tracks success/fail counts for generation attempts."""

    def __init__(self) -> None:
        self.total: int = 0
        self.success: int = 0
        self.fail: int = 0
        self.timeouts: int = 0

    def record_success(self) -> None:
        self.total += 1
        self.success += 1

    def record_fail(self) -> None:
        self.total += 1
        self.fail += 1

    def record_timeout(self) -> None:
        self.total += 1
        self.fail += 1
        self.timeouts += 1

    def to_dict(self) -> Dict[str, int]:
        return {
            "total": self.total,
            "success": self.success,
            "fail": self.fail,
            "timeouts": self.timeouts
        }


@dataclass
class TimeoutContext:
    """Context manager for enforcing generation timeouts."""
    timeout_seconds: float
    logger: logging.Logger

    def __enter__(self) -> None:
        self._original_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(int(self.timeout_seconds))

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self._original_handler)
        return False

    @staticmethod
    def _timeout_handler(signum, frame) -> None:
        raise GenerationTimeoutError("Generation attempt timed out")


def run_with_timeout(
    func: Callable,
    timeout_seconds: float,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with a timeout.
    Raises GenerationTimeoutError if the function exceeds the timeout.
    """
    with TimeoutContext(timeout_seconds, logger):
        return func(*args, **kwargs)


def log_sample_status(
    counter: SampleCounter,
    output_path: Path,
    details: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Log sample counts and details to a JSON file.
    Ensures the log file exists and counts sum correctly.
    """
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "counts": counter.to_dict(),
        "details": details or []
    }

    # Verify invariant: total == success + fail
    assert log_entry["counts"]["total"] == (
        log_entry["counts"]["success"] + log_entry["counts"]["fail"]
    ), "Log invariant violated: total != success + fail"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)

    log_operation(
        "log_sample_status",
        output=str(output_path),
        total=counter.total,
        success=counter.success,
        fail=counter.fail
    )


def save_summary(counter: SampleCounter, output_path: Path) -> None:
    """Save a summary of generation attempts to a JSON file."""
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": counter.to_dict()
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def enforce_minimum_samples(
    counter: SampleCounter,
    minimum: int,
    strategy: str,
    prompt_id: str
) -> bool:
    """
    Check if the minimum number of successful samples has been reached.
    Returns True if minimum is met, False otherwise.
    """
    met = counter.success >= minimum
    log_operation(
        "enforce_minimum_samples",
        strategy=strategy,
        prompt_id=prompt_id,
        minimum=minimum,
        current=counter.success,
        met=met
    )
    return met


def main() -> None:
    """
    CLI entry point for testing timeout and logging functionality.
    Simulates a generation pipeline with timeout and logging.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Timeout and logging test")
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/generation_log.json",
        help="Path to the output log file"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for each generation"
    )
    parser.add_argument(
        "--simulate-fail",
        action="store_true",
        help="Simulate a failure scenario"
    )
    args = parser.parse_args()

    counter = SampleCounter()
    output_path = Path(args.output)

    def mock_generation():
        """Mock generation function that may timeout or fail."""
        if args.simulate_fail:
            time.sleep(args.timeout + 2)  # Force timeout
        else:
            time.sleep(0.1)  # Quick success
        return "Generated text"

    for i in range(3):
        try:
            result = run_with_timeout(mock_generation, args.timeout)
            counter.record_success()
            log_operation("generation_success", attempt=i, result=result)
        except GenerationTimeoutError as e:
            counter.record_timeout()
            log_operation("generation_timeout", attempt=i, error=str(e))
        except Exception as e:
            counter.record_fail()
            log_operation("generation_fail", attempt=i, error=str(e))

    log_sample_status(counter, output_path)
    print(f"Log written to {output_path}")
    print(f"Counts: {counter.to_dict()}")


if __name__ == "__main__":
    main()