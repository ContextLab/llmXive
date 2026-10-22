"""Group‑aware stratified splitting for the corrosion pipeline (T005).

This module implements a 5‑fold ``StratifiedGroupKFold`` split that
respects the ``source_id`` grouping column while stratifying on the
original composition label (``composition_original``). The resulting
train/validation index pairs are serialized to
``data/processed/splits.pkl`` for downstream consumption.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_cleaned_dataset() -> pd.DataFrame:
    """Load the cleaned dataset produced by ``ingest``."""
    cleaned_path = paths.data("processed", "cleaned_dataset.csv")
    if not cleaned_path.is_file():
        log.error("Cleaned dataset not found at %s", cleaned_path)
        raise FileNotFoundError(cleaned_path)
    return pd.read_csv(cleaned_path)

def _prepare_stratify_labels(df: pd.DataFrame) -> pd.Series:
    """Return a series suitable for stratification.

    The ingestion step creates a ``composition_original`` column that
    holds the raw material label (e.g. ``Fe``, ``Al``). We use this as
    the stratification target because it directly reflects the
    composition class distribution.
    """
    if "composition_original" not in df.columns:
        log.error(
            "Column 'composition_original' missing; cannot stratify."
        )
        raise KeyError("composition_original")
    return df["composition_original"]

def _create_splits(
    df: pd.DataFrame,
    n_splits: int = 5,
    random_state: int = 42,
) -> List[Tuple[List[int], List[int]]]:
    """Generate train/validation index pairs.

    Parameters
    ----------
    df :
        Cleaned DataFrame containing at least ``source_id`` and
        ``composition_original``.
    n_splits :
        Number of folds (default 5).
    random_state :
        Seed for reproducibility.

    Returns
    -------
    List of (train_idx, val_idx) tuples where each element is a list of
    integer row positions.
    """
    groups = df["source_id"].values
    y = _prepare_stratify_labels(df).values
    cv = StratifiedGroupKFold(
        n_splits=n_splits, shuffle=True, random_state=random_state
    )
    splits: List[Tuple[List[int], List[int]]] = []
    for train_idx, val_idx in cv.split(df, y, groups):
        splits.append((train_idx.tolist(), val_idx.tolist()))
    return splits

def _save_splits(splits: List[Tuple[List[int], List[int]]]) -> None:
    """Serialize the split indices to ``splits.pkl``."""
    out_path = paths.data("processed", "splits.pkl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as fh:
        pickle.dump(splits, fh)
    log.info("Stratified group splits written to %s", out_path)

def main(argv: List[str] | None = None) -> int:
    """Entry point for ``python -m src.pipeline.split``.

    The function loads the cleaned data, creates a 5‑fold
    ``StratifiedGroupKFold`` split, and persists the indices.
    """
    try:
        df = _load_cleaned_dataset()
        splits = _create_splits(df, n_splits=5, random_state=42)
        _save_splits(splits)
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        log.exception("Failed to create stratified group splits: %s", exc)
        return 1

if __name__ == "__main__":
    import sys

    sys.exit(main())
