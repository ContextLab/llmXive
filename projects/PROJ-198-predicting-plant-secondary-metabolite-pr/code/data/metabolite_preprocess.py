"""
Metabolite preprocessing utilities.

This module implements the **T008** task: harmonise metabolite identifiers,
add a pseudo‑count, and log‑transform abundance values.

The script scans all metabolite TSV files under ``data/raw/<species>/metabolites.tsv``,
concatenates them, normalises the identifier column to InChIKey (lower‑case
``inchikey``), adds a pseudo‑count of 1 to the raw abundance, applies a natural
logarithm, and writes the result to ``data/processed/metabolite_harmonized.csv``.
The output contains only the identifier column and a numeric ``abundance_log``
column, with values typically in the range 0–10.

The module can also be imported and the :func:`harmonize_metabolites` function
called directly with explicit input and output paths.
"""

import logging
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd

# llmxive_toolkit utilities for consistent path handling and logging
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

def _discover_metabolite_files(root: Path) -> List[Path]:
    """
    Recursively locate all ``metabolites.tsv`` files under ``root``.

    Parameters
    ----------
    root: Path
        Base directory (typically ``data/raw``).

    Returns
    -------
    List[Path]
        Sorted list of file paths.
    """
    pattern = root.glob("*/*/metabolites.tsv")
    files = sorted([p for p in pattern if p.is_file()])
    if not files:
        logger.warning(f"No metabolite TSV files found under {root}")
    return files

def _load_and_validate(file_path: Path) -> pd.DataFrame:
    """
    Load a single metabolite TSV file and ensure required columns exist.

    Expected columns (case‑insensitive):
        - species
        - abundance (numeric)
        - InChIKey (or inchikey)

    Parameters
    ----------
    file_path: Path

    Returns
    -------
    pd.DataFrame
    """
    logger.debug(f"Loading metabolite file: {file_path}")
    df = pd.read_csv(file_path, sep="\t", dtype=str)

    # Normalise column names to lower case for easier handling
    df.columns = [c.lower() for c in df.columns]

    required = {"species", "abundance", "inchikey"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Metabolite file {file_path} is missing required columns: {missing}"
        )

    # Convert abundance to numeric (coerce errors to NaN)
    df["abundance"] = pd.to_numeric(df["abundance"], errors="coerce")
    if df["abundance"].isnull().any():
        raise ValueError(
            f"Non‑numeric abundance values detected in {file_path}"
        )

    return df

def harmonize_metabolites(
    input_paths: Iterable[Path],
    output_path: Path,
) -> pd.DataFrame:
    """
    Core harmonisation routine.

    Parameters
    ----------
    input_paths: Iterable[Path]
        Paths to raw metabolite TSV files.
    output_path: Path
        Destination CSV file for the harmonised data.

    Returns
    -------
    pd.DataFrame
        DataFrame containing ``inchikey`` and ``abundance_log`` columns.
    """
    logger.info("Starting metabolite harmonisation")
    dfs = [_load_and_validate(p) for p in input_paths]

    if not dfs:
        raise RuntimeError("No metabolite data provided for harmonisation")

    # Concatenate all species‑level tables
    combined = pd.concat(dfs, ignore_index=True)

    # Add pseudo‑count of 1 and apply natural log
    combined["abundance_log"] = np.log(combined["abundance"] + 1)

    # Keep only the identifier and the transformed abundance
    result = combined[["inchikey", "abundance_log"]].copy()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info(f"Harmonised metabolite data written to {output_path}")

    return result

def main() -> None:
    """
    CLI entry point.

    The script automatically discovers metabolite files under ``data/raw``.
    The output is written to ``data/processed/metabolite_harmonized.csv``.
    """
    # Resolve project‑relative paths using llmxive_toolkit helpers
    raw_root = paths.data("raw")
    output_file = paths.data("processed", "metabolite_harmonized.csv")

    metabolite_files = _discover_metabolite_files(raw_root)
    if not metabolite_files:
        logger.error("No metabolite files found – nothing to process.")
        return

    try:
        harmonize_metabolites(metabolite_files, output_file)
    except Exception as exc:
        logger.exception(f"Metabolite harmonisation failed: {exc}")

if __name__ == "__main__":
    # When executed as a script, run the full pipeline
    main()
