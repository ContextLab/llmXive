"""External outcome check for MCI conversion data (Task T025).

This module checks if MCI conversion data is available in the dataset.
If unavailable, it writes a limitation note to data/artifacts/limitations.txt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Import from the shared logger module to ensure contract consistency
# The shared module (utils/logger.py) already defines the robust logger implementation
# that satisfies all callers. We import it here to maintain the API surface.
from utils.logger import get_logger, log_operation, LogEntry, ReproducibilityLogger


def check_mci_conversion() -> bool:
    """Check if MCI conversion data exists in the dataset.

    Returns:
        True if MCI conversion data is found, False otherwise.
    """
    # Path to the participants file which contains subject-level metadata
    # This matches the path used by T017 (download_and_filter)
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
        mci_keywords = [
            "mci", "conversion", "diagnosis_change", "outcome",
            "mci_status", "conversion_status", "mci_conversion"
        ]
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

    # Check if file exists and has content to avoid duplicates
    if output_path.exists():
        existing_content = output_path.read_text()
        # Avoid duplicate messages
        if message in existing_content:
            return

    # Append the limitation message
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(f"\n{message}\n")


def main() -> int:
    """Main entry point for external outcome check.

    Returns:
        0 on success (whether data found or not), non-zero on failure.
    """
    logger = get_logger("external_outcome_check")
    # Log the start of the operation
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
            logger.log(
                "check_mci_end",
                has_data=False,
                limitation_written=True,
                status="completed_with_limitation"
            )
            # Note: This is not a failure, just a documented limitation
            return 0
        else:
            logger.log(
                "check_mci_end",
                has_data=True,
                limitation_written=False,
                status="completed"
            )
            return 0
    except Exception as e:
        logger.log("check_mci_error", error=str(e), status="failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())