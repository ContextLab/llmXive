"""Data saver utilities for knot dataset.

This module provides functions to persist raw knot records and cleaned
DataFrames to disk in the project's data directories.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Mapping

import pandas as pd

def save_raw_and_cleaned_data(
    raw_records: Iterable[Mapping[str, object]],
    cleaned_df: pd.DataFrame,
    raw_path: Path = Path("data/raw/knot_atlas_raw.json"),
    cleaned_path: Path = Path("data/processed/knots_cleaned.csv"),
) -> None:
    """Save raw JSON records and a cleaned CSV file.

    Parameters
    ----------
    raw_records: Iterable of mapping objects representing the raw records.
    cleaned_df: pandas.DataFrame containing cleaned knot data.
    raw_path: Destination path for the raw JSON file.
    cleaned_path: Destination path for the cleaned CSV file.
    """
    # Ensure parent directories exist
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)

    # Write raw records as pretty‑printed JSON
    with raw_path.open("w", encoding="utf-8") as f:
        json.dump(list(raw_records), f, indent=2, ensure_ascii=False)

    # Write cleaned DataFrame to CSV
    cleaned_df.to_csv(cleaned_path, index=False)