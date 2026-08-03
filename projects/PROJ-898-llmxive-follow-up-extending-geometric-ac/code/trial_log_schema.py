"""
Trial Log Schema and Logger.

Defines the schema for trial logging and provides utilities for writing logs.
"""
import csv
import os
from typing import Dict, List, Optional, Any, TextIO
from dataclasses import dataclass, asdict
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class TrialLogEntry:
    """
    Schema for a single trial log entry.

    Attributes:
        trial_id: Unique identifier for the trial.
        step: Step number within the trial.
        success: Whether the trial was successful.
        infeasible: Whether the solver returned infeasible.
        timeout: Whether the trial timed out.
        latency_ms: Execution time in milliseconds.
    """
    trial_id: str
    step: int
    success: bool
    infeasible: bool
    timeout: bool
    latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return asdict(self)


class TrialLogger:
    """
    Logger for trial results.
    """
    def __init__(self, log_path: str = "data/results/trial_log.csv"):
        """
        Initialize the trial logger.

        Args:
            log_path: Path to the CSV log file.
        """
        self.log_path = log_path
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create the log file with headers if it doesn't exist."""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_fieldnames())
                writer.writeheader()
                logger.info(f"Created trial log file: {self.log_path}")

    def _get_fieldnames(self) -> List[str]:
        """Return the list of fieldnames for the CSV."""
        return ["trial_id", "step", "success", "infeasible", "timeout", "latency_ms"]

    def log(self, entry: TrialLogEntry) -> None:
        """
        Log a trial entry.

        Args:
            entry: The trial log entry to log.
        """
        with open(self.log_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self._get_fieldnames())
            writer.writerow(entry.to_dict())

    def get_schema_description(self) -> str:
        """
        Get a human-readable description of the schema.

        Returns:
            String describing the schema.
        """
        return """
        Trial Log Schema:
        - trial_id: str - Unique identifier for the trial
        - step: int - Step number within the trial
        - success: bool - Whether the trial was successful
        - infeasible: bool - Whether the solver returned infeasible
        - timeout: bool - Whether the trial timed out
        - latency_ms: float - Execution time in milliseconds
        """


def get_schema_description() -> str:
    """
    Get a human-readable description of the schema.

    Returns:
        String describing the schema.
    """
    return TrialLogger().get_schema_description()


def verify_schema(log_path: str = "data/results/trial_log.csv") -> bool:
    """
    Verify that the log file has the correct schema.

    Args:
        log_path: Path to the log file.

    Returns:
        True if schema is valid, False otherwise.
    """
    if not os.path.exists(log_path):
        logger.error(f"Log file not found: {log_path}")
        return False

    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        expected_fields = TrialLogger(). _get_fieldnames()

        if reader.fieldnames != expected_fields:
            logger.error(f"Schema mismatch. Expected: {expected_fields}, Got: {reader.fieldnames}")
            return False

    return True


def main() -> None:
    """
    Main entry point for testing the trial logger.
    """
    logging.basicConfig(level=logging.INFO)

    # Create logger
    logger_instance = TrialLogger("data/results/trial_log.csv")

    # Log a test entry
    entry = TrialLogEntry(
        trial_id="test_001",
        step=1,
        success=True,
        infeasible=False,
        timeout=False,
        latency_ms=150.5
    )
    logger_instance.log(entry)
    logger.info("Logged test entry.")

    # Verify schema
    if verify_schema():
        logger.info("Schema verification passed.")
    else:
        logger.error("Schema verification failed.")


if __name__ == "__main__":
    main()