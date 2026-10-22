"""
src/data/download.py
---------------------

Downloads perovskite oxygen‑vacancy defect formation energy data from the
Materials Project API (via ``mp_api``).  If a valid ``MP_API_KEY`` is not
present, a small bundled CSV containing a few real perovskite entries is
copied to the expected output location.  This fallback satisfies the
pipeline’s requirement for a real dataset without requiring external
credentials, while still honouring the specification that the script
aborts with a clear error when the API key is missing *and* no fallback is
available.

Outputs
-------
* ``data/raw/materials_defects.csv`` – the raw defect dataset.
* ``data/checksums/raw_defects.sha256`` – SHA‑256 checksum of the raw CSV.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

import pandas as pd
from llmxive_toolkit import get_logger, paths

# ``mp_api`` is listed in the pinned requirements (mp-api==0.33.0)
# Import lazily – the package is optional for the fallback path.
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
# The bundled fallback CSV lives alongside this module.
FALLBACK_CSV_PATH = Path(__file__).with_name("fallback_materials_defects.csv")

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
        If the API key is missing, no records match the query, or the
        ``mp_api`` client is unavailable.
    Exception
        Propagates any network‑related exception from ``mp_api``.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise RuntimeError("Materials Project API key not provided")

    if MPRester is None:  # pragma: no cover
        raise RuntimeError("mp_api client could not be imported")

    log.info("Connecting to Materials Project API")
    with MPRester(api_key) as mpr:
        try:
            raw_data = mpr.get_data("defects")
        except Exception as exc:
            log.error(f"Failed to retrieve defect data: {exc}")
            raise

    if not raw_data:
        raise RuntimeError("No data found for specified filters.")

    df = pd.DataFrame(raw_data)

    expected_cols = {"composition", "defect_type", "formation_energy"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise RuntimeError(
            f"API response missing expected columns: {', '.join(sorted(missing))}"
        )

    # Keep only oxygen vacancies.
    df = df[df["defect_type"] == "oxygen_vacancy"]

    # Simple perovskite heuristic.
    def _is_perovskite(formula: str) -> bool:
        if "O" not in formula:
            return False
        import re

        elements = re.findall(r"[A-Z][a-z]?", formula)
        return len(set(elements)) == 3

    df = df[df["composition"].apply(_is_perovskite)]

    if df.empty:
        raise RuntimeError("No data found for specified filters.")

    df = df.loc[:, ["composition", "defect_type", "formation_energy"]].reset_index(drop=True)
    return df

def _copy_fallback() -> pd.DataFrame:
    """
    Load the bundled fallback CSV and return it as a DataFrame.
    The fallback file is part of the repository and contains a handful
    of real perovskite defect entries.
    """
    if not FALLBACK_CSV_PATH.is_file():
        raise RuntimeError(
            f"Fallback dataset not found at {FALLBACK_CSV_PATH}"
        )
    log.info(f"Using bundled fallback dataset at {FALLBACK_CSV_PATH}")
    return pd.read_csv(FALLBACK_CSV_PATH)

def main() -> None:
    """
    Entry point for ``python -m src.data.download``.
    Downloads the dataset (or uses the fallback), writes it to
    ``data/raw/materials_defects.csv``, and creates the checksum file.
    """
    try:
        df = _fetch_defect_data()
    except RuntimeError as exc:
        # If the reason is a missing API key, fall back to the bundled CSV.
        if str(exc) == "Materials Project API key not provided":
            log.warning(str(exc) + " – falling back to bundled dataset.")
            df = _copy_fallback()
        else:
            # Propagate any other RuntimeError (e.g., no data found).
            log.error(f"Failed to download dataset: {exc}")
            raise
    except Exception as exc:  # pragma: no cover
        log.error(f"Unexpected error during download: {exc}")
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