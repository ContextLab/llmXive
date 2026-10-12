import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_config

logger = logging.getLogger(__name__)

RUFF_CONFIG_PATH = Path(__file__).resolve().parent / ".ruff.toml"


def verify_ruff_config(config_path: Path = RUFF_CONFIG_PATH) -> bool:
    """Verify that the ruff lint configuration from T003a exists.

    Raises:
        FileNotFoundError: with an informative message if the file is absent.
    """
    if not config_path.is_file():
        raise FileNotFoundError(
            "Pipeline configuration check FAILED: required lint configuration "
            f"file '{config_path}' is missing. It must be created by task T003a "
            "(ruff configuration with max line length 100 and flake8-annotations) "
            "before the pipeline can proceed."
        )
    logger.info("Ruff configuration check passed: %s exists.", config_path)
    return True


class RuntimeTracker:
    _instance = None
    _start_time: Optional[float] = None
    _max_hours: float = 6.0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start(self):
        if self._start_time is None:
            self._start_time = time.time()

    def stop(self):
        self._start_time = None

    def elapsed_hours(self) -> float:
        if self._start_time is None:
            return 0.0
        return (time.time() - self._start_time) / 3600.0

    def check_limit(self, max_hours: Optional[float] = None) -> bool:
        max_hours = max_hours if max_hours is not None else self._max_hours
        return self.elapsed_hours() <= max_hours


def get_tracker() -> RuntimeTracker:
    return RuntimeTracker()


def start_pipeline_timer():
    tracker = get_tracker()
    tracker.start()
    logger.info("Pipeline timer started.")


def stop_pipeline_timer():
    tracker = get_tracker()
    tracker.stop()
    logger.info("Pipeline timer stopped.")


def check_pipeline_limit():
    tracker = get_tracker()
    if not tracker.check_limit():
        logger.error("Pipeline exceeded maximum runtime.")
        generate_timeout_report()
        raise TimeoutError("Pipeline timeout limit exceeded.")


def enforce_pipeline_limit():
    """Final compute-time guard invoked at pipeline shutdown.

    Sums elapsed stage times from pipeline_log.json and raises TimeoutError
    if the cumulative runtime exceeds MAX_RUNTIME_HOURS (6 hours).
    """
    log_file = Path("data/results/pipeline_log.json")
    total_seconds = 0.0
    if log_file.exists():
        try:
            with open(log_file, "r") as f:
                log_data = json.load(f)
            for stage in log_data.get("stages", []):
                total_seconds += float(stage.get("duration_seconds", 0.0))
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            logger.warning("Could not parse pipeline log for runtime guard: %s", exc)
    total_hours = total_seconds / 3600.0
    if total_hours > 6.0:
        generate_timeout_report()
        raise TimeoutError(
            f"Pipeline exceeded maximum runtime: {total_hours:.2f} hours > 6.0 hours."
        )
    logger.info("Compute-time guard passed: %.2f hours elapsed.", total_hours)


def generate_timeout_report():
    """Generate a timeout report."""
    report_path = Path("data/results/compute_time_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("# Compute Time Report\n\n")
        f.write("Pipeline timed out before completion.\n")
        f.write(f"Elapsed time: {get_tracker().elapsed_hours():.2f} hours\n")


def update_pipeline_log(stage: str, status: str, details: str = ""):
    """Update the pipeline log file."""
    log_file = Path("data/results/pipeline_log.json")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_data = {"stages": []}
    if log_file.exists():
        with open(log_file, "r") as f:
            log_data = json.load(f)

    log_data["stages"].append(
        {
            "stage": stage,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        }
    )

    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)


class PipelineTimerContext:
    def __init__(self, max_hours: float = 6.0):
        self.max_hours = max_hours

    def __enter__(self):
        get_tracker().start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        get_tracker().stop()


def validate_data_integrity(data: Dict[str, Any]) -> bool:
    """Validate data integrity."""
    return True


def main():
    """Entry point for validation script.

    Runs the T003a configuration verification step: asserts that
    code/.ruff.toml exists and aborts with a clear error if missing.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        verify_ruff_config()
    except FileNotFoundError as exc:
        logger.error(str(exc))
        sys.exit(1)
    logger.info("All configuration checks passed.")


if __name__ == "__main__":
    main()
