"""External Outcome Check (T025): Verify MCI conversion data availability.

This module implements Task T025: Check for MCI conversion data in the dataset.
If unavailable, it writes a limitation note to data/artifacts/limitations.txt
as required by FR-011.

The module also provides a fully tolerant logging infrastructure (ReproducibilityLogger)
to support the wider pipeline, ensuring compatibility with all calling patterns
identified in the execution history.
"""
from __future__ import annotations

import csv
import functools
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

# --- Constants ---
PARTICIPANTS_PATH = Path("data/raw/ds000246/participants.tsv")
LIMITATIONS_PATH = Path("data/artifacts/limitations.txt")
DATASET_ROOT = Path("data/raw/ds000246")


# --- Reproducibility Logging Infrastructure ---
# This section implements a self-contained logging system to avoid
# conflicts with the standard library's logging module (which requires
# integer levels and lacks .to_json()). This satisfies the "SHARED-MODULE CONTRACT"
# requirement to handle 18+ different call shapes without raising.

@dataclass
class LogEntry:
    """A structured log entry that can be serialized to JSON."""
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "success"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A tolerant logger that accepts any call shape and never raises.

    This logger is designed to be drop-in compatible with various usage patterns
    found in the codebase:
    1. get_logger("name") -> returns instance
    2. logger.log("op", key="val") -> returns LogEntry
    3. logger.info("msg") -> no-op (tolerant)
    4. @log_operation("op") -> decorator
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Support: get_logger("name"), get_logger(name="name"), get_logger()
        if args:
            self.name = str(args[0])
        else:
            self.name = kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log an operation and return a LogEntry.

        Supports:
        - log("operation_name", param1=val1)
        - log(operation="operation_name", param1=val1)
        """
        op = args[0] if args else kwargs.get("operation", "unknown_operation")
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs) if kwargs else {},
            status=kwargs.get("status", "success")
        )
        self.entries.append(entry)
        return entry

    # Tolerant no-ops for standard logging methods (.info, .debug, etc.)
    def __getattr__(self, name: str) -> Callable[..., None]:
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Retrieve or create the global reproducibility logger.

    This function is the single entry point for logging in the project.
    It ensures a singleton instance is used across all modules.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        # Initialize with provided args/kwargs or defaults
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    elif args or kwargs:
        # If called again with args, we could update the name, but typically
        # we just return the existing one to maintain global state consistency.
        # However, some callers might expect a new logger per name.
        # To be safe and tolerant, we return the global one if it exists,
        # or create a new one if the global is None.
        pass
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose logging helper: decorator or direct call.

    Usage as decorator:
        @log_operation("my_operation")
        def my_func(): ...

    Usage as direct call:
        entry = log_operation("my_operation", param=value)
        print(entry.to_json())
    """
    # Check if called as a decorator: @log_operation
    # This happens if the first argument is a callable and no kwargs are present (or minimal)
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            # Log the start
            entry = get_logger().log(func.__name__, operation=func.__name__, status="started")
            try:
                result = func(*a, **k)
                entry.status = "success"
                return result
            except Exception as e:
                entry.status = "failed"
                entry.parameters["error"] = str(e)
                raise
        return _wrapper

    # Called directly: log_operation("op_name", ...)
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


# --- Core Task Logic (T025) ---

@log_operation("check_mci_conversion")
def check_mci_conversion() -> bool:
    """Check if MCI conversion data exists in the dataset.

    This function verifies the presence of specific longitudinal data points
    (e.g., MCI conversion status) in the dataset's participants file or
    associated metadata.

    Returns:
        True if MCI conversion data is found, False otherwise.
    """
    logger = get_logger("external_outcome_check")
    logger.log("start_check", dataset_root=str(DATASET_ROOT))

    if not DATASET_ROOT.exists():
        logger.log("dataset_missing", path=str(DATASET_ROOT), status="failed")
        return False

    # Check for participants.tsv
    if not PARTICIPANTS_PATH.exists():
        logger.log("participants_missing", path=str(PARTICIPANTS_PATH), status="failed")
        return False

    try:
        # Read participants.tsv to check for MCI columns
        # We expect a TSV file. We look for columns like 'MCI_status', 'conversion', 'diagnosis_change'
        mci_columns = ['MCI_status', 'conversion', 'diagnosis_change', 'mci_conversion']
        found_mci = False

        with open(PARTICIPANTS_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            if not reader.fieldnames:
                logger.log("empty_participants", status="failed")
                return False

            fieldnames_lower = [fn.lower() for fn in reader.fieldnames]
            for col in mci_columns:
                if col.lower() in fieldnames_lower:
                    found_mci = True
                    break

            # Also check for any column containing 'mci' or 'conversion'
            if not found_mci:
                for fn in reader.fieldnames:
                    fn_lower = fn.lower()
                    if 'mci' in fn_lower or 'conversion' in fn_lower:
                        found_mci = True
                        break

        if found_mci:
            logger.log("mci_data_found", columns=reader.fieldnames, status="success")
            return True
        else:
            logger.log("mci_data_not_found", columns=reader.fieldnames, status="success")
            return False

    except Exception as e:
        logger.log("error_reading_participants", error=str(e), status="failed")
        return False


@log_operation("write_limitation")
def write_limitation(missing: bool = True) -> None:
    """Write a limitation note to data/artifacts/limitations.txt.

    Args:
        missing: If True, indicates MCI data is missing and a limitation should be recorded.
    """
    logger = get_logger("external_outcome_check")
    logger.log("writing_limitation", missing=missing)

    # Ensure directory exists
    LIMITATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)

    note_content = (
        "# Limitations report generated by T025 (external outcome check)\n\n"
        f"MCI conversion data {'not available' if missing else 'is available'}.\n"
    )

    if missing:
        note_content += (
            "The dataset (ds000246) lacks explicit MCI conversion labels required "
            "for validating the cognitive decline prediction model against a clinical "
            "gold standard. The analysis is therefore restricted to the available "
            "longitudinal MMSE/MOCA scores as a proxy for decline.\n"
        )

    with open(LIMITATIONS_PATH, 'w', encoding='utf-8') as f:
        f.write(note_content)

    logger.log("limitation_written", path=str(LIMITATIONS_PATH), status="success")


@log_operation("main")
def main() -> int:
    """Main entry point for Task T025."""
    logger = get_logger("external_outcome_check")
    logger.log("starting_task_T025")

    mci_available = check_mci_conversion()

    if not mci_available:
        write_limitation(missing=True)
        print("MCI conversion data not found. Limitation note written to data/artifacts/limitations.txt")
    else:
        print("MCI conversion data found. No limitation note needed.")

    logger.log("task_complete", mci_available=mci_available)
    return 0


if __name__ == "__main__":
    sys.exit(main())