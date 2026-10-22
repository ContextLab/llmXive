"""
src/data/download.py
---------------------

Downloads perovskite oxygen‑vacancy defect formation energy data from the
Materials Project API (via ``mp_api``). The file is written to
``data/raw/materials_defects.csv`` and a SHA‑256 checksum file is created in
``data/checksums/raw_defects.sha256``.

Requirements
------------
• Abort with clear error ``"Materials Project API key not provided"`` if the
  ``MP_API_KEY`` environment variable is missing.
• Abort with ``"No data found for specified filters."`` if the API query
  returns zero records.
• If the API cannot be reached, raise the exception (do **not** fall back
  to synthetic data).
• Compute SHA‑256 checksum for the output file.
"""

import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
from llmxive_toolkit import get_logger, paths

# mp_api is listed in the pinned requirements (mp-api==0.33.0)
from mp_api.client import MPRester

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
RAW_CSV_PATH = paths.data("raw", "materials_defects.csv")
CHECKSUM_PATH = paths.data("checksums", "raw_defects.sha256")


def _write_checksum(file_path: Path, checksum_path: Path) -> None:
    """Write the SHA‑256 checksum of *file_path* to *checksum_path*."""
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    checksum_path.write_text(sha256.hexdigest())
    log.info(f"Checksum written to {checksum_path}")


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
        If the API key is missing or no records match the query.
    Exception
        Propagates any network‑related exception from ``mp_api``.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise RuntimeError("Materials Project API key not provided")

    log.info("Connecting to Materials Project API")
    with MPRester(api_key) as mpr:
        # ``mpr.get_data`` returns a list of dicts for the requested collection.
        # The collection name for defects is ``defects``.
        try:
            raw_data = mpr.get_data("defects")
        except Exception as exc:
            log.error(f"Failed to retrieve defect data: {exc}")
            raise

    if not raw_data:
        raise RuntimeError("No data found for specified filters.")

    # Convert to DataFrame and keep only the columns we need.
    df = pd.DataFrame(raw_data)

    # Ensure required columns exist; rename if the API uses different keys.
    expected_cols = {"composition", "defect_type", "formation_energy"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise RuntimeError(
            f"API response missing expected columns: {', '.join(sorted(missing))}"
        )

    # Filter to oxygen vacancies only (the schema restricts defect_type).
    df = df[df["defect_type"] == "oxygen_vacancy"]

    # At this stage we may have many entries that are not perovskites.
    # A simple heuristic: keep formulas that contain exactly three distinct
    # element symbols (ABX3) and end with ``O`` for the X site.
    # This is not a strict validation but removes obvious non‑perovskite
    # entries while keeping the majority of the dataset.
    def _is_perovskite(formula: str) -> bool:
        # Basic check: must contain exactly three element symbols.
        # We rely on the fact that perovskite formulas are of the form
        # A B X3 (e.g., BaTiO3). The presence of "O" is required for the
        # oxygen vacancy.
        if "O" not in formula:
            return False
        # Count distinct alphabetic groups (ignoring numbers).
        import re

        elements = re.findall(r"[A-Z][a-z]?", formula)
        return len(set(elements)) == 3

    df = df[df["composition"].apply(_is_perovskite)]

    if df.empty:
        raise RuntimeError("No data found for specified filters.")

    # Keep only the three required columns and reset the index.
    df = df.loc[:, ["composition", "defect_type", "formation_energy"]].reset_index(drop=True)
    return df


def main() -> None:
    """
    Entry point for ``python -m src.data.download``.
    Downloads the dataset, writes it to ``data/raw/materials_defects.csv``,
    and creates the checksum file.
    """
    try:
        df = _fetch_defect_data()
    except Exception as exc:
        log.error(f"Failed to download dataset: {exc}")
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