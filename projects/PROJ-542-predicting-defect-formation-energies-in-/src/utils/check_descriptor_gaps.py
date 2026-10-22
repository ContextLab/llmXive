"""
src/utils/check_descriptor_gaps.py
----------------------------------

Utilities to detect missing descriptor values in the feature matrix.
The public API consists of ``_descriptor_columns`` (returns the list of
expected descriptor column names) and ``check_descriptor_gaps`` (scans a
CSV and writes a log, raising ``RuntimeError`` if gaps are found).
"""

from pathlib import Path
from typing import List, Tuple

import pandas as pd
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _descriptor_columns() -> List[str]:
    """
    Return the list of expected descriptor column names (excluding the target).
    """
    sites = ["A", "B", "X"]
    descriptors = [
        "atomic_radius",
        "electronegativity",
        "oxidation_state",
        "valence_electrons",
    ]
    return [f"{site}_{desc}" for site in sites for desc in descriptors]

def _find_gaps(df: pd.DataFrame) -> List[Tuple[int, str]]:
    """
    Identify rows with missing descriptor values.

    Returns:
        A list of tuples ``(row_index, column_name)`` for each missing entry.
    """
    descriptor_cols = _descriptor_columns()
    gaps = []
    for col in descriptor_cols:
        missing_idx = df[df[col].isna()].index.tolist()
        for idx in missing_idx:
            gaps.append((idx, col))
    return gaps

def check_descriptor_gaps(features_path: Path = None, log_path: Path = None) -> None:
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

    df = pd.read_csv(features_path)
    gaps = _find_gaps(df)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        if not gaps:
            f.write("No descriptor gaps found.\\n")
            return
        f.write("Descriptor gaps detected:\\n")
        for row_idx, col in gaps:
            f.write(f"- Row {row_idx} (column {col})\\n")

    if gaps:
        raise RuntimeError("Descriptor gaps detected – see descriptor_gaps.log")