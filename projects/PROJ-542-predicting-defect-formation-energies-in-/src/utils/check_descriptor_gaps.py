"""
src/utils/check_descriptor_gaps.py
----------------------------------

Scan the processed feature matrix for missing descriptor values and log any gaps.
If any missing values are found, the pipeline aborts with a clear error message
(fulfilling FR‑006).

The script is intended to be called from the pipeline after feature generation.
It uses the standard ``paths`` helper to locate ``data/processed/features.csv``
and writes a log file ``data/processed/descriptor_gaps.log``.
"""

from pathlib import Path
from typing import List, Tuple

import pandas as pd

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _descriptor_columns() -> List[str]:
    """Return the list of expected descriptor column names (excluding the target)."""
    sites = ["A", "B", "X"]
    descriptors = ["atomic_radius", "electronegativity", "oxidation_state", "valence_electrons"]
    return [f"{site}_{desc}" for site in sites for desc in descriptors]

def _find_gaps(df: pd.DataFrame) -> List[Tuple[int, str]]:
    """
    Identify rows with missing descriptor values.

    Returns:
        A list of tuples ``(row_index, column_name)`` for each missing entry.
    """
    missing = []
    for col in _descriptor_columns():
        if col not in df.columns:
            # If a column is completely absent, treat every row as missing for that column.
            missing.extend([(idx, col) for idx in df.index])
            continue
        # ``isna`` catches both ``NaN`` and ``None``.
        rows_with_nan = df[df[col].isna()].index.tolist()
        missing.extend([(idx, col) for idx in rows_with_nan])
    return missing

# ----------------------------------------------------------------------
# Main API
# ----------------------------------------------------------------------
def check_descriptor_gaps(
    features_path: Path = None,
    log_path: Path = None,
) -> None:
    """
    Scan ``features_path`` for missing descriptor values and write a log.

    If any gaps are detected, a ``RuntimeError`` is raised with a clear
    message, causing the pipeline to abort.

    Parameters
    ----------
    features_path: Path, optional
        Path to ``features.csv``. If omitted, the default location
        ``data/processed/features.csv`` is used.
    log_path: Path, optional
        Destination for the gap log. Defaults to
        ``data/processed/descriptor_gaps.log``.
    """
    if features_path is None:
        features_path = paths.data("processed", "features.csv")
    if log_path is None:
        log_path = paths.data("processed", "descriptor_gaps.log")

    if not features_path.is_file():
        raise FileNotFoundError(f"Features file not found at {features_path}")

    df = pd.read_csv(features_path)

    # Identify gaps
    gaps = _find_gaps(df)

    # Ensure the log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the log file
    with log_path.open("w", encoding="utf-8") as f:
        if not gaps:
            f.write("No descriptor gaps found.\n")
            log.info("Descriptor gap check passed – no missing values.")
            return
        f.write("Descriptor gaps detected:\n")
        for row_idx, col_name in gaps:
            # Use the composition column as an identifier if present
            identifier = (
                df.at[row_idx, "composition"]
                if "composition" in df.columns
                else f"row_{row_idx}"
            )
            f.write(f"- Row {row_idx} ({identifier}): missing {col_name}\n")
        log.error(f"Descriptor gaps found in {len(gaps)} entries; aborting pipeline.")
        raise RuntimeError(
            f"Descriptor gaps detected ({len(gaps)} missing values). "
            f"See {log_path} for details."
        )

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point: ``python -m src.utils.check_descriptor_gaps``.
    """
    try:
        check_descriptor_gaps()
    except Exception as exc:
        # Print the error to stderr and exit with a non‑zero status.
        log.error(str(exc))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
