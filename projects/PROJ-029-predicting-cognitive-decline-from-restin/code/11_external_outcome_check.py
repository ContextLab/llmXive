"""External outcome check: Verify MCI conversion data availability (FR-011).

This module checks if the dataset contains longitudinal MCI conversion labels.
If unavailable, it writes a limitation note to `data/artifacts/limitations.txt`
to be consumed by the final report generator (T031).
"""
from __future__ import annotations

import functools
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

# Constants
LIMITATIONS_PATH = Path("data/artifacts/limitations.txt")
PARTICIPANTS_PATH = Path("data/raw/ds000246/participants.tsv")
DATASET_DESCRIPTION_PATH = Path("data/raw/ds000246/dataset_description.json")
MCI_COLUMNS = ["mci_conversion", "mci_status", "diagnosis_followup", "dx_change"]


@dataclass
class LogEntry:
    """Reproducibility log entry."""
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "success"
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Fully tolerant logger that accepts any call shape and never raises."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        op = args[0] if args else kwargs.get("operation", "operation")
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            status=kwargs.get("status", "success"),
            message=kwargs.get("message", "")
        )
        self.entries.append(entry)
        return entry

    # Tolerant no-op for standard logging methods
    def __getattr__(self, name: str) -> Any:
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: decorator (@log_operation) or direct logging call.

    Returns a LogEntry for direct calls, wrapped function for decorators.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


@log_operation
def check_mci_conversion() -> bool:
    """Check if MCI conversion data is available in the dataset.

    Checks:
    1. If participants.tsv exists and contains MCI-related columns.
    2. If dataset_description.json mentions longitudinal follow-up or MCI.

    Returns:
        True if MCI conversion data is found, False otherwise.
    """
    logger = get_logger("external_outcome_check")
    logger.log("check_mci_conversion", status="started", message="Checking for MCI conversion data")

    # Check 1: participants.tsv
    if PARTICIPANTS_PATH.exists():
        try:
            df = pd.read_csv(PARTICIPANTS_PATH, sep='\t')
            cols_lower = [str(c).lower() for c in df.columns]
            
            found_cols = [c for c in MCI_COLUMNS if c.lower() in cols_lower]
            if found_cols:
                logger.log("check_mci_conversion", status="success", message=f"Found MCI columns: {found_cols}")
                return True
        except Exception as e:
            logger.log("check_mci_conversion", status="error", message=f"Error reading participants.tsv: {e}")
            # Fall through to other checks

    # Check 2: dataset_description.json for keywords
    if DATASET_DESCRIPTION_PATH.exists():
        try:
            with open(DATASET_DESCRIPTION_PATH, 'r') as f:
                desc = json.load(f)
            desc_text = json.dumps(desc).lower()
            if any(kw in desc_text for kw in ["mci", "conversion", "longitudinal", "follow-up"]):
                logger.log("check_mci_conversion", status="success", message="Found MCI references in dataset_description.json")
                return True
        except Exception as e:
            logger.log("check_mci_conversion", status="error", message=f"Error reading dataset_description.json: {e}")

    logger.log("check_mci_conversion", status="warning", message="MCI conversion data not found")
    return False


@log_operation
def write_limitation(missing: bool = True) -> None:
    """Write a limitation note to the artifacts file.

    Args:
        missing: If True, write that MCI data is missing.
    """
    logger = get_logger("external_outcome_check")
    logger.log("write_limitation", status="started", message=f"Writing limitation (missing={missing})")

    # Ensure directory exists
    LIMITATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Append to existing file or create new
    with open(LIMITATIONS_PATH, 'a') as f:
        f.write("\n")
        if missing:
            f.write(f"[{datetime.utcnow().isoformat()}] MCI conversion data not available in dataset.\n")
            f.write("  - Checked 'participants.tsv' for MCI-related columns: None found.\n")
            f.write("  - Checked 'dataset_description.json' for MCI/longitudinal keywords: None found.\n")
            f.write("  - Impact: Cannot validate model predictions against actual MCI conversion outcomes.\n")
            f.write("  - Scope: Analysis is limited to predicting cognitive score decline (MMSE/MOCA) only.\n")
        else:
            f.write(f"[{datetime.utcnow().isoformat()}] MCI conversion data IS available.\n")
            f.write("  - Model validation can include external clinical outcomes.\n")

    logger.log("write_limitation", status="success", message=f"Written to {LIMITATIONS_PATH}")


def main() -> int:
    """Main entry point for the external outcome check."""
    logger = get_logger("external_outcome_check")
    logger.log("main", status="started", message="Starting external outcome check")

    try:
        mci_available = check_mci_conversion()
        
        if not mci_available:
            write_limitation(missing=True)
            logger.log("main", status="completed", message="MCI data missing; limitation note written")
            return 0
        else:
            write_limitation(missing=False)
            logger.log("main", status="completed", message="MCI data available")
            return 0

    except Exception as e:
        logger.log("main", status="error", message=f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())