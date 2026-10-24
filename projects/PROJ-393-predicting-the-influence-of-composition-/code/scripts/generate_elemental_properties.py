"""
Script to generate a verified elemental properties reference CSV.
The CSV is written to ``data/raw/elemental_properties.csv`` and a SHA‑256
checksum entry is appended to ``data/checksums.txt``.

The data are sourced from the public "periodic-table" dataset hosted on
GitHub (https://github.com/datasets/periodic-table). Only the elements
required for the Heusler‑alloy study are retained, and the columns are
reduced to those needed by the feature‑engineering code:

- ``element``               – chemical symbol (e.g., ``Fe``)
- ``electronegativity``    – Pauling electronegativity
- ``atomic_radii``         – atomic radius in picometres
- ``valence_electrons``    – number of valence electrons (outer‑shell count)

The script is safe to re‑run: it overwrites the CSV and updates the
checksum entry atomically.
"""

import csv
import hashlib
import logging
from pathlib import Path

import pandas as pd
import requests

from llmxive_toolkit import get_logger, paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# URL of the raw CSV file containing a full periodic‑table dataset.
PERIODIC_TABLE_URL = (
    "https://raw.githubusercontent.com/datasets/periodic-table/master/data/periodic-table.csv"
)

# Elements that must be present for the Heusler‑alloy pipeline.
REQUIRED_ELEMENTS = [
    "Mn", "Co", "Fe", "Ga", "Al",
    "Ni", "Cu", "Sn", "In", "Ti", "V"
]

# Output locations (project‑relative)
OUTPUT_CSV = paths.data("raw", "elemental_properties.csv")
CHECKSUM_FILE = paths.data("checksums.txt")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _download_periodic_table(url: str) -> pd.DataFrame:
    """Download the periodic‑table CSV and return it as a DataFrame."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.read_csv(pd.compat.StringIO(response.text))

def _extract_relevant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the columns required by the pipeline and rename them to the
    expected schema.
    
    The source dataset uses the following column names:
    - ``symbol``               → element symbol
    - ``electronegativity``   → Pauling EN (may contain NaN)
    - ``atomic_radius``       → atomic radius in pm
    - ``group``               → group number (1‑18)
    
    ``valence_electrons`` is derived from the group number for the
    elements of interest (the outer‑shell electron count).
    """
    # Select and rename columns
    subset = df[["symbol", "electronegativity", "atomic_radius", "group"]].copy()
    subset.rename(
        columns={
            "symbol": "element",
            "electronegativity": "electronegativity",
            "atomic_radius": "atomic_radii",
            "group": "valence_electrons",
        },
        inplace=True,
    )
    return subset

def _filter_required_elements(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows whose ``element`` is in ``REQUIRED_ELEMENTS``."""
    return df[df["element"].isin(REQUIRED_ELEMENTS)].reset_index(drop=True)

def _write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write the DataFrame to CSV with the exact header order required."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)

def _write_checksum(csv_path: Path, checksum_path: Path) -> None:
    """
    Compute the SHA‑256 checksum of ``csv_path`` and write (or replace)
    the corresponding line in ``checksum_path``.
    """
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    # Compute hash
    sha256 = hashlib.sha256()
    with csv_path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    digest = sha256.hexdigest()

    # Read existing lines (if any) and replace the line for this file
    lines = []
    if checksum_path.exists():
        with checksum_path.open("r") as f:
            lines = f.readlines()
        lines = [ln for ln in lines if not ln.strip().endswith(csv_path.name)]

    # Append the new checksum line
    lines.append(f"{digest}  {csv_path.relative_to(paths.root)}\n")

    # Write back atomically
    temp_path = checksum_path.with_suffix(".tmp")
    with temp_path.open("w") as f:
        f.writelines(lines)
    temp_path.replace(checksum_path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    logger = get_logger(__name__)
    logger.info("Generating elemental_properties.csv...")

    # 1. Download source dataset
    df_raw = _download_periodic_table(PERIODIC_TABLE_URL)

    # 2. Keep only the columns we need and rename them
    df_subset = _extract_relevant_columns(df_raw)

    # 3. Filter to the required Heusler‑alloy elements
    df_needed = _filter_required_elements(df_subset)

    # 4. Write the CSV file
    _write_csv(df_needed, OUTPUT_CSV)
    logger.info(f"Wrote elemental properties to {OUTPUT_CSV}")

    # 5. Update the checksum manifest
    _write_checksum(OUTPUT_CSV, CHECKSUM_FILE)
    logger.info(f"Updated checksum file {CHECKSUM_FILE}")

if __name__ == "__main__":
    main()