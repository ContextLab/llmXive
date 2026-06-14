"""
Reproducibility logging framework for tracking pipeline operations.

This module provides structured logging for all operations in the knot complexity
analysis pipeline to ensure reproducibility and auditability.

Each log entry contains:
  - timestamp: ISO 8601 formatted timestamp of the operation
  - operation: Description of what operation was performed
  - input_file: Path to input file(s) (can be None)
  - output_file: Path to output file(s) (can be None)
  - parameters: Dictionary of parameters used in the operation
  - status: One of 'success', 'failure', 'partial'
  - duration_ms: Duration of operation in milliseconds
"""

import json
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager


@dataclass
class LogEntry:
    """A single log entry for reproducibility tracking."""

    timestamp: str
    operation: str
    input_file: Optional[Union[str, List[str]]] = None
    output_file: Optional[Union[str, List[str]]] = None
    parameters: Optional[Dict[str, Any]] = None
    status: str = "success"
    duration_ms: float = 0.0

    def __post_init__(self):
        """Validate and normalize log entry fields."""
        if self.status not in ("success", "failure", "partial"):
            raise ValueError(f"Invalid status: {self.status}. Must be 'success', 'failure', or 'partial'")

        # Normalize single strings to lists for file fields
        if isinstance(self.input_file, str):
            self.input_file = [self.input_file]
        if isinstance(self.output_file, str):
            self.output_file = [self.output_file]

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert log entry to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class ReproducibilityLogger:
    """
    Logger for tracking reproducibility-critical operations.

    This logger records all operations with their inputs, outputs, parameters,
    and timing information to enable full pipeline reproducibility.
    """

    def __init__(self, log_file: Optional[Union[str, Path]] = None):
        """
        Initialize the reproducibility logger.

        Args:
            log_file: Optional path to write logs to. If None, logs are kept in memory.
        """
        self.log_file: Optional[Path] = Path(log_file) if log_file else None
        self.entries: List[LogEntry] = []
        self._start_times: Dict[str, float] = {}

    def log(
        self,
        operation: str,
        input_file: Optional[Union[str, List[str]]] = None,
        output_file: Optional[Union[str, List[str]]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        status: str = "success",
        duration_ms: Optional[float] = None
    ) -> LogEntry:
        """
        Create and record a log entry.

        Args:
            operation: Description of the operation performed
            input_file: Input file path(s)
            output_file: Output file path(s)
            parameters: Dictionary of operation parameters
            status: Operation status ('success', 'failure', 'partial')
            duration_ms: Operation duration in milliseconds

        Returns:
            The created LogEntry
        """
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            operation=operation,
            input_file=input_file,
            output_file=output_file,
            parameters=parameters or {},
            status=status,
            duration_ms=duration_ms or 0.0
        )
        self.entries.append(entry)
        self._write_entry(entry)
        return entry

    def _write_entry(self, entry: LogEntry) -> None:
        """Write a log entry to file if log_file is configured."""
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry.to_json() + "\n")

    def start_timer(self, operation: str) -> None:
        """
        Start timing an operation.

        Args:
            operation: Unique identifier for the operation being timed
        """
        self._start_times[operation] = time.perf_counter()

    def stop_timer(self, operation: str) -> float:
        """
        Stop timing an operation and return duration.

        Args:
            operation: Unique identifier for the operation being timed

        Returns:
            Duration in seconds
        """
        if operation not in self._start_times:
            raise KeyError(f"No timer started for operation: {operation}")

        duration = (time.perf_counter() - self._start_times[operation]) * 1000  # Convert to ms
        del self._start_times[operation]
        return duration

    @contextmanager
    def timed_operation(
        self,
        operation: str,
        input_file: Optional[Union[str, List[str]]] = None,
        output_file: Optional[Union[str, List[str]]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for timing and logging an operation.

        Usage:
            with logger.timed_operation("parse_knots", input_file="data.json"):
                # perform operation
            # automatically logs on exit

        Args:
            operation: Description of the operation
            input_file: Input file path(s)
            output_file: Output file path(s)
            parameters: Operation parameters

        Yields:
            None
        """
        self.start_timer(operation)
        status = "success"
        try:
            yield
        except Exception as e:
            status = "failure"
            raise
        finally:
            duration_ms = self.stop_timer(operation) if operation in self._start_times else 0.0
            self.log(
                operation=operation,
                input_file=input_file,
                output_file=output_file,
                parameters=parameters,
                status=status,
                duration_ms=duration_ms
            )

    def get_entries(self) -> List[LogEntry]:
        """Return all logged entries."""
        return self.entries.copy()

    def get_entries_by_status(self, status: str) -> List[LogEntry]:
        """Return entries filtered by status."""
        return [e for e in self.entries if e.status == status]

    def get_entries_by_operation(self, operation: str) -> List[LogEntry]:
        """Return entries filtered by operation name."""
        return [e for e in self.entries if e.operation == operation]

    def to_json(self, indent: int = 2) -> str:
        """Export all entries to JSON array."""
        return json.dumps([e.to_dict() for e in self.entries], indent=indent, default=str)

    def save(self, path: Optional[Union[str, Path]] = None) -> None:
        """
        Save all log entries to a file.

        Args:
            path: Optional path to save to. Uses log_file if not specified.
        """
        save_path = Path(path) if path else self.log_file
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(self.to_json())

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ReproducibilityLogger":
        """
        Load log entries from a JSON file.

        Args:
            path: Path to the JSON log file

        Returns:
            ReproducibilityLogger instance with loaded entries
        """
        path = Path(path)
        logger = cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            entry = LogEntry(
                timestamp=item["timestamp"],
                operation=item["operation"],
                input_file=item.get("input_file"),
                output_file=item.get("output_file"),
                parameters=item.get("parameters"),
                status=item.get("status", "success"),
                duration_ms=item.get("duration_ms", 0.0)
            )
            logger.entries.append(entry)
        return logger


# Module-level convenience functions
_default_logger: Optional[ReproducibilityLogger] = None


def get_logger(log_file: Optional[Union[str, Path]] = None) -> ReproducibilityLogger:
    """
    Get or create the default reproducibility logger.

    Args:
        log_file: Optional path to write logs to

    Returns:
        ReproducibilityLogger instance
    """
    global _default_logger
    if _default_logger is None or log_file:
        _default_logger = ReproducibilityLogger(log_file)
    return _default_logger


def log_operation(
    operation: str,
    input_file: Optional[Union[str, List[str]]] = None,
    output_file: Optional[Union[str, List[str]]] = None,
    parameters: Optional[Dict[str, Any]] = None,
    status: str = "success",
    duration_ms: Optional[float] = None
) -> LogEntry:
    """
    Log an operation using the default logger.

    Args:
        operation: Description of the operation
        input_file: Input file path(s)
        output_file: Output file path(s)
        parameters: Operation parameters
        status: Operation status
        duration_ms: Duration in milliseconds

    Returns:
        The created LogEntry
    """
    return get_logger().log(operation, input_file, output_file, parameters, status, duration_ms)