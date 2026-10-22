"""
src/data/download.py
---------------------

Downloads perovskite oxygen‑vacancy defect formation energy data from the
Materials Project API (via ``mp_api``).  The script aborts with clear
error messages when required conditions are not met, in accordance with
the specification for task **T002**.

Behaviour
----------
* If the ``MP_API_KEY`` environment variable is missing, a
  ``RuntimeError`` with the message ``"Materials Project API key not provided"``
  is raised.
* The script queries the Materials Project ``defects`` endpoint for entries
  with ``defect_type == "oxygen_vacancy"``.
* A simple perovskite heuristic is applied (the formula must contain
  oxygen and exactly three distinct elements).
* If the filtered result set is empty, a ``RuntimeError`` with the
  message ``"No data found for specified filters."`` is raised.
* The resulting DataFrame (columns ``composition``, ``defect_type``,
  ``formation_energy``) is written to ``data/raw/materials_defects.csv``.
* A SHA‑256 checksum of the CSV is written to
  ``data/checksums/raw_defects.sha256``.
* All I/O paths are created via ``llmxive_toolkit.paths`` to guarantee
  correct project‑relative locations.

The implementation deliberately avoids any synthetic fallback – if the
API cannot be reached or the required key is missing, the script fails
loudly, satisfying the “no silent synthetic data” rule.
"""

import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
from llmxive_toolkit import get_logger, paths

# ``mp_api`` is declared in the pinned requirements.
try:
    from mp_api.client import MPRester
except Exception:  # pragma: no cover
    MPRester = None  # type: ignore

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
RAW_CSV_PATH = paths.data("raw", "materials_defects.csv")
CHECKSUM_PATH = paths.data("checksums", "raw_defects.sha256")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _write_checksum(file_path: Path, checksum_path: Path) -> None:
    """Write the SHA‑256 checksum of *file_path* to *checksum_path*."""
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    checksum_path.write_text(sha256.hexdigest())
    log.info(f"Checksum written to {checksum_path}")

def _is_perovskite(formula: str) -> bool:
    """
    Very small heuristic to decide whether a formula is a perovskite
    (ABX₃) containing oxygen.

    Returns True if ``O`` is present and the formula contains exactly
    three distinct element symbols.
    """
    if "O" not in formula:
        return False
    import re

    elements = re.findall(r"[A-Z][a-z]?", formula)
    return len(set(elements)) == 3

def _fetch_defect_data() -> pd.DataFrame:
    """
    Query the Materials Project API for oxygen‑vacancy defect formation
    energies in perovskites.

    Returns
    -------
    pd.DataFrame
        Columns: ``composition``, ``defect_type``, ``formation_energy``.

    Raises
    ------
    RuntimeError
        * If the API key is missing.
        * If no records match the filters.
    Exception
        Propagates any network‑related exception from ``mp_api``.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise RuntimeError("Materials Project API key not provided")

    if MPRester is None:
        raise RuntimeError("mp_api client could not be imported")

    # Use a context manager to ensure proper cleanup.
    with MPRester(api_key) as mpr:
        log.info("Querying Materials Project defects endpoint")
        try:
            # The ``defects`` endpoint provides a ``search`` method.
            # We request only the fields we need to keep the payload small.
            raw_records = mpr.defects.search(
                defect_type="oxygen_vacancy",
                fields=["composition", "defect_type", "formation_energy"],
            )
        except Exception as exc:
            log.error(f"Failed to retrieve defect data: {exc}")
            raise

    if not raw_records:
        raise RuntimeError("No data found for specified filters.")

    df = pd.DataFrame(raw_records)

    # Ensure the expected columns are present.
    expected_cols = {"composition", "defect_type", "formation_energy"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise RuntimeError(
            f"API response missing expected columns: {', '.join(sorted(missing))}"
        )

    # Apply the perovskite heuristic.
    df = df[df["composition"].apply(_is_perovskite)]

    if df.empty:
        raise RuntimeError("No data found for specified filters.")

    # Keep only the three required columns and reset the index.
    df = df.loc[:, ["composition", "defect_type", "formation_energy"]].reset_index(drop=True)
    return df

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for ``python -m src.data.download``.
    Downloads the dataset, writes it to ``data/raw/materials_defects.csv``,
    and creates the checksum file.
    """
    try:
        df = _fetch_defect_data()
    except Exception as exc:
        # Propagate any exception – the caller (or CI) will see a non‑zero
        # exit status and the explicit error message.
        log.error(str(exc))
        raise

    # Ensure the target directory exists.
    RAW_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CSV_PATH, index=False)
    log.info(f"Raw dataset written to {RAW_CSV_PATH}")

    # Compute and write checksum.
    _write_checksum(RAW_CSV_PATH, CHECKSUM_PATH)

if __name__ == "__main__":
    # When executed as a script we exit with a non‑zero code on failure.
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)