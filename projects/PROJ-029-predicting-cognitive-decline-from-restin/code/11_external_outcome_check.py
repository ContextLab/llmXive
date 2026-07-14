"""Check for external outcome data (MCI conversion) in the OpenNeuro dataset.

This script inspects the BIDS participants.tsv file for a column that would
indicate conversion from mild cognitive impairment (MCI) to dementia.  If such
a column is missing or contains no data, a limitation note is written to
``data/artifacts/limitations.txt`` so that downstream reporting can include it.

The script is deliberately lightweight – it does not attempt to download or
preprocess any imaging data.  Its sole purpose is to verify the presence of
an external outcome variable required by the research question.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List

from utils.logger import get_logger
from utils.io import ensure_dir

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Relative to the project root.  The BIDS dataset is expected to be present
# under ``data/raw/ds000246`` after the ``01_download_and_filter`` step.
PARTICIPANTS_TSV = Path("data/raw/ds000246/participants.tsv")
LIMITATIONS_FILE = Path("data/artifacts/limitations.txt")

# Column name that would contain the MCI conversion label.  The exact name
# may differ across datasets; we check a few common variants.
MCI_COLUMNS = [
    "MCI_conversion",       # Preferred canonical name
    "MCI_Conversion",       # Capitalised variant
    "conversion_status",    # Generic variant
    "diagnosis_change",     # Generic variant
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _read_participants_tsv(path: Path) -> List[dict]:
    """Read a BIDS participants.tsv file into a list of dictionaries.

    Parameters
    ----------
    path: Path
        Path to the TSV file.

    Returns
    ----------
    List[dict]
        Each row as a dictionary keyed by column names.
    """
    if not path.is_file():
        raise FileNotFoundError(f"participants.tsv not found at {path}")

    with path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)

def check_mci_availability(participants: Iterable[dict]) -> bool:
    """Return ``True`` if the dataset contains any non‑empty MCI conversion data.

    The function looks for any of the column names listed in ``MCI_COLUMNS``.
    If a column is found, it checks whether at least one row has a non‑empty
    value (ignoring whitespace).

    Parameters
    ----------
    participants: Iterable[dict]
        Rows from ``participants.tsv``.

    Returns
    ----------
    bool
        ``True`` if usable MCI conversion data is present, else ``False``.
    """
    logger = get_logger("external_outcome_check")
    logger.debug("Checking for MCI conversion columns in participants.tsv")

    # Identify which column (if any) is present
    available_columns = set(participants[0].keys()) if participants else set()
    mci_column = None
    for col in MCI_COLUMNS:
        if col in available_columns:
            mci_column = col
            break

    if not mci_column:
        logger.info("No MCI conversion column found in participants.tsv")
        return False

    logger.info(f"Found MCI conversion column: {mci_column}")

    # Check for at least one non‑empty entry
    for row in participants:
        value = row.get(mci_column, "").strip()
        if value:
            logger.info("MCI conversion data is present for at least one subject")
            return True

    logger.info("MCI conversion column exists but contains no data")
    return False

def write_limitation_note(path: Path, note: str) -> None:
    """Write a limitation note to ``path``, creating parent directories as needed."""
    logger = get_logger("external_outcome_check")
    ensure_dir(path.parent)
    logger.debug(f"Writing limitation note to {path}")
    with path.open("w", encoding="utf-8") as f:
        f.write(note + "\n")
    logger.info(f"Limitation note written to {path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Execute the external outcome check.

    Returns
    -------
    int
        Exit code (0 for success, 1 for unexpected error).
    """
    logger = get_logger("external_outcome_check")
    logger.info("Starting external outcome (MCI conversion) check")

    try:
        participants = _read_participants_tsv(PARTICIPANTS_TSV)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        # If the participants file itself is missing, we treat this as a
        # limitation – the dataset is incomplete for our purposes.
        note = (
            "Limitation: participants.tsv not found; unable to verify MCI conversion data. "
            "External outcome analysis omitted."
        )
        write_limitation_note(LIMITATIONS_FILE, note)
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        logger.error(f"Unexpected error while reading participants.tsv: {exc}")
        return 1

    has_mci = check_mci_availability(participants)

    if not has_mci:
        note = (
            "Limitation: MCI conversion data not available in the dataset. "
            "External outcome analysis omitted."
        )
        write_limitation_note(LIMITATIONS_FILE, note)
    else:
        logger.info("MCI conversion data available – no limitation note needed.")

    logger.info("External outcome check completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
