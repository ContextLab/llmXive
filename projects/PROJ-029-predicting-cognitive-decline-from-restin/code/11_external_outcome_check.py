"""Check for external outcome (MCI conversion) data availability.

This script is part of the predictive modeling pipeline. It inspects the
downloaded OpenNeuro dataset (``ds000246``) for any file that contains
Mild Cognitive Impairment (MCI) conversion information. If such data are
not present, a plain‑text limitation note is written to
``data/artifacts/limitations.txt`` so that downstream reporting can cite
the missing external outcome.

The script is invoked by the quick‑start run‑book and must exit cleanly
with status ``0``.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from utils.logger import get_logger
from utils.io import ensure_dir

def _project_root() -> Path:
    """Resolve the project root directory relative to this file.

    This file lives in ``code/``, so the project root is its parent.
    """
    return Path(__file__).resolve().parents[1]

def _candidate_paths() -> list[Path]:
    """Return a list of candidate file paths that could hold MCI conversion data."""
    raw_dir = _project_root() / "data" / "raw" / "ds000246"
    return [
        raw_dir / "clinical" / "MCI_conversion.tsv",
        raw_dir / "MCI_conversion.tsv",
        raw_dir / "participants.tsv",  # sometimes conversion info is embedded here
    ]

def _has_mci_column_in_participants(participants_path: Path) -> bool:
    """Return True if the participants.tsv file contains a column that likely stores MCI conversion info.

    The OpenNeuro participants file may include a column such as
    ``MCI_conversion`` or ``MCI``. We perform a simple heuristic: if any
    column name (case‑insensitive) contains the substring ``mci`` we treat
    it as containing the needed information.
    """
    try:
        with participants_path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader, [])
            for col in header:
                if "mci" in col.lower():
                    return True
    except Exception:
        # If we cannot read the file for any reason, assume it does not contain the data.
        return False
    return False

def check_mci_availability() -> bool:
    """Return ``True`` if any known MCI conversion file is present and contains data.

    For explicit conversion files we only require existence. For the
    ``participants.tsv`` fallback we also require a column that appears to
    store MCI conversion information.
    """
    for path in _candidate_paths():
        if not path.is_file():
            continue
        # If the candidate is participants.tsv, perform a lightweight content check.
        if path.name == "participants.tsv":
            if _has_mci_column_in_participants(path):
                return True
            # No relevant column → treat as not containing conversion data.
            continue
        # For dedicated conversion files we assume their presence means data are available.
        return True
    return False

def write_limitation_note() -> None:
    """Write a plain‑text limitation note to ``data/artifacts/limitations.txt``."""
    out_dir = _project_root() / "data" / "artifacts"
    ensure_dir(out_dir)
    note_path = out_dir / "limitations.txt"

    note = (
        "Limitation: The dataset does not contain MCI conversion data. "
        "Consequently, external outcome validation could not be performed. "
        "All downstream conclusions should be interpreted accordingly."
    )

    # Overwrite any existing note to keep the file up‑to‑date
    note_path.write_text(note + "\n", encoding="utf-8")

def main() -> None:
    """Entry point for the script."""
    logger = get_logger("external_outcome_check")
    logger.info("Starting external outcome check.")

    if check_mci_availability():
        logger.info("MCI conversion data found – no limitation note written.")
    else:
        logger.warning("MCI conversion data NOT found – writing limitation note.")
        write_limitation_note()

    logger.info("External outcome check completed.")
    # Exit cleanly with status 0
    sys.exit(0)

if __name__ == "__main__":
    main()