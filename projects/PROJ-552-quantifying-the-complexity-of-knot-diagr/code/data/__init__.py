"""Top‑level helpers for the ``code.data`` package."""

from pathlib import Path
import json
import pandas as pd

from .data_saver import save_raw_and_cleaned_data

RAW_JSON_PATH = Path("data/raw/knot_atlas_raw.json")
CLEANED_CSV_PATH = Path("data/processed/knots_cleaned.csv")


def load_cleaned_knots() -> pd.DataFrame:
    """
    Load the cleaned knot catalogue produced by the download‑parser pipeline.

    Returns
    -------
    pandas.DataFrame
        The processed knot records.

    Raises
    ------
    FileNotFoundError
        If the cleaned CSV does not exist yet.
    """
    if not CLEANED_CSV_PATH.is_file():
        raise FileNotFoundError(f"Cleaned data file not found: {CLEANED_CSV_PATH}")
    return pd.read_csv(CLEANED_CSV_PATH)


# Backwards‑compatibility shim – many older modules import this name directly.
def save_raw_and_cleaned_data(raw_records, cleaned_df) -> None:  # pragma: no cover
    """Delegate to the implementation in ``data_saver``."""
    return save_raw_and_cleaned_data(raw_records, cleaned_df)