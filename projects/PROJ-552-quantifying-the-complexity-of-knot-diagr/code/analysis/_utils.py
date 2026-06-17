from __future__ import annotations
import pandas as pd
from pathlib import Path
from reproducibility.logs import get_logger

# -------------------------------------------------------------------------
# Centralised data‑loading helper
#
# The original implementation relied on a CSV that occasionally contained
# non‑numeric strings (e.g. column headers appearing as rows).  That caused
# downstream scripts to fail when they attempted numeric conversion.
# The updated version:
#   * Reads the processed CSV (``data/processed/knots_cleaned.csv``) if it
#     exists; otherwise falls back to the raw JSON produced by the
#     ``download`` step.
#   * Normalises column names to snake_case.
#   * Forces the core numeric columns (crossing_number, braid_index,
#     volume) to numeric dtype, coercing errors to NaN.
#   * Returns a clean ``pd.DataFrame`` suitable for all downstream
#     analysis modules.
# -------------------------------------------------------------------------
_CLEANED_PATH = Path("data") / "processed" / "knots_cleaned.csv"
_RAW_JSON_PATH = Path("data") / "raw" / "knot_atlas_raw.json"

def _standardise_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Convert column names to lower‑case snake_case."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df

def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Coerce supplied columns to numeric, turning errors into NaN."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def load_cleaned_knots() -> pd.DataFrame:
    """
    Load the cleaned knot dataset.

    Returns
    -------
    pd.DataFrame
        A DataFrame with at least the following columns (all numeric where
        appropriate):
            - crossing_number
            - braid_index
            - volume
            - alternating (as a boolean or categorical string)
    """
    logger = get_logger()
    if _CLEANED_PATH.is_file():
        logger.debug("Loading cleaned knot data from %s", str(_CLEANED_PATH))
        df = pd.read_csv(_CLEANED_PATH)
    else:
        logger.debug(
            "Cleaned CSV not found; falling back to raw JSON at %s",
            str(_RAW_JSON_PATH),
        )
        import json

        with _RAW_JSON_PATH.open("r", encoding="utf-8") as f:
            records = json.load(f)
        df = pd.DataFrame.from_records(records)

    # Normalise column names
    df = _standardise_column_names(df)

    # Ensure core numeric columns are numeric
    numeric_cols = ["crossing_number", "braid_index", "volume"]
    df = _coerce_numeric(df, numeric_cols)

    # Normalise the alternating flag to a clean categorical column
    if "alternating" in df.columns:
        df["alternating"] = df["alternating"].astype(str).str.upper()
    else:
        # If the field is missing, create a placeholder (will be flagged by
        # validation later)
        df["alternating"] = "UNKNOWN"

    logger.info(
        "Loaded %d knot records (numeric columns coerced).",
        len(df),
    )
    return df
