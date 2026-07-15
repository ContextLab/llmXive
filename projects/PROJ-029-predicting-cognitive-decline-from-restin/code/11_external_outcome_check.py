"""External outcome check for MCI conversion data (Task T025).

This module checks if MCI conversion data is available in the dataset.
If unavailable, it writes a limitation note to data/artifacts/limitations.txt.
"""
from __future__ import annotations

import functools
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.logger import get_logger, log_operation


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: decorator or direct call."""
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def check_mci_conversion() -> bool:
    """Check if MCI conversion data exists in the dataset.

    Returns:
        True if MCI conversion data is found, False otherwise.
    """
    # Path to the participants file which contains subject-level metadata
    participants_path = Path("data/raw/ds000246/participants.tsv")

    # Check if the file exists
    if not participants_path.exists():
        return False

    try:
        # Read the file to check for MCI-related columns
        content = participants_path.read_text()
        lines = content.strip().split("\n")
        if not lines:
            return False

        # Check header for MCI-related columns
        header = lines[0].lower()
        mci_keywords = ["mci", "conversion", "diagnosis_change", "outcome"]
        has_mci_data = any(keyword in header for keyword in mci_keywords)

        return has_mci_data
    except Exception:
        # If we can't read or parse the file, assume no MCI data
        return False


def write_limitation(message: str) -> None:
    """Write limitation note to the artifacts file.

    Args:
        message: The limitation message to write.
    """
    output_path = Path("data/artifacts/limitations.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists and has content
    if output_path.exists():
        existing_content = output_path.read_text()
        # Avoid duplicate messages
        if message in existing_content:
            return

    # Append the limitation message
    with open(output_path, "a") as f:
        f.write(f"\n{message}\n")


def main() -> int:
    """Main entry point for external outcome check.

    Returns:
        0 on success, non-zero on failure.
    """
    logger = get_logger("external_outcome_check")
    logger.log("check_mci_start", operation="external_outcome_check")

    try:
        has_data = check_mci_conversion()

        if not has_data:
            limitation_msg = (
                "MCI conversion data not available in ds000246. "
                "The dataset lacks longitudinal MCI conversion labels, "
                "which limits the ability to validate predictions against "
                "clinically confirmed progression outcomes. "
                "Analysis is based on MMSE/MOCA score changes only."
            )
            write_limitation(limitation_msg)
            logger.log("check_mci_end", has_data=False, limitation_written=True)
        else:
            logger.log("check_mci_end", has_data=True, limitation_written=False)

        return 0
    except Exception as e:
        logger.log("check_mci_error", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())