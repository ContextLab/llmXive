"""Check for external outcome (MCI conversion) data availability.

If the dataset does not contain MCI conversion information, a limitation
note is written to ``data/artifacts/limitations.txt``. This script is
invoked by the quickstart run‑book and must complete without error,
producing the declared artifact.
"""
from __future__ import annotations

from __future__ import annotations

import csv
from pathlib import Path

from utils.logger import get_logger
from utils.io import ensure_dir


def _project_root() -> Path:
    """
    Resolve the project root directory relative to this file.
    This file lives in ``code/``, so the project root is its parent.
    """
    return Path(__file__).resolve().parents[1]


def check_mci_availability() -> bool:
    """Return ``True`` if any known MCI conversion file is present.

    The OpenNeuro dataset ``ds000246`` may store conversion information in
    several possible locations. We check a handful of conventional paths.
    """
    raw_dir = _project_root() / "data" / "raw" / "ds000246"

    candidate_paths = [
        raw_dir / "clinical" / "MCI_conversion.tsv",
        raw_dir / "MCI_conversion.tsv",
        raw_dir / "participants.tsv",  # sometimes conversion info is embedded here
    ]

    return any(p.is_file() for p in candidate_paths)


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
    note_path.write_text(note + "\\n", encoding="utf-8")


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
    # Exit cleanly
    sys.exit(0)

if __name__ == "__main__":
    main()