"""
Output writer utilities for the simulation pipeline.
Handles writing raw p-values to CSV and loading them for downstream analysis.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Import the tolerant logger defined in the project
from code.simulation.logging_config import get_logger

logger = get_logger(__name__)


def ensure_output_directory() -> None:
    """
    Ensure that the directory for simulation outputs exists.
    Uses the project's path helper to create the folder if missing.
    """
    # The path helper creates parent directories automatically
    from llmxive_toolkit import paths
    paths.data("simulation")
    logger.log("output_directory_ensured", path=str(paths.data("simulation")))


def _csv_path() -> Path:
    """Return the absolute Path object for the raw p‑values CSV."""
    from llmxive_toolkit import paths
    return paths.data("simulation", "p_values_raw.csv")


def write_p_values_raw(
    results: List[Dict[str, Any]],
    *,
    append: bool = False,
    header: Optional[List[str]] = None,
) -> None:
    """
    Write a list of result dictionaries to the raw p‑values CSV.

    Parameters
    ----------
    results: List[Dict[str, Any]]
        Each dict must be serialisable to a flat CSV row.
    append: bool, default False
        If True, rows are appended to an existing file; otherwise the file
        is overwritten (or created if it does not exist).
    header: Optional[List[str]]
        Explicit column order. If omitted, the keys of the first result
        dict define the column order.
    """
    if not results:
        logger.log("write_p_values_raw_skip", reason="no results")
        return

    csv_file = _csv_path()
    mode = "a" if append else "w"
    file_exists = csv_file.exists()

    # Determine header order
    if header is None:
        header = list(results[0].keys())

    logger.log(
        "write_p_values_raw_start",
        path=str(csv_file),
        rows=len(results),
        mode=mode,
        header=header,
    )

    with open(csv_file, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)

        # Write header only if creating a new file or if the file is empty
        if not append or not file_exists:
            writer.writeheader()

        for row in results:
            # Ensure the row only contains the declared columns
            filtered = {col: row.get(col, "") for col in header}
            writer.writerow(filtered)

    logger.log("write_p_values_raw_complete", path=str(csv_file), rows_written=len(results))


def load_p_values_raw(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the raw p‑values CSV into a pandas DataFrame.

    Parameters
    ----------
    filepath: Optional[str]
        Path to the CSV file. If omitted, the default simulation location is used.

    Returns
    -------
    pd.DataFrame
        DataFrame with the raw simulation results.
    """
    if filepath is None:
        csv_path = _csv_path()
    else:
        csv_path = Path(filepath)

    logger.log("load_p_values_raw_start", path=str(csv_path))

    if not csv_path.is_file():
        logger.log("load_p_values_raw_missing", path=str(csv_path))
        raise FileNotFoundError(f"Raw p‑values file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    logger.log("load_p_values_raw_complete", rows=len(df))
    return df
