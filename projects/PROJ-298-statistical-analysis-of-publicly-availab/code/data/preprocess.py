"""
Preprocess Stack Overflow PostsTags data.

This script implements task T009:
  - Normalizes tag strings (lower‑case, trim)
  - Aggregates monthly tag counts for 2015‑01‑01 → 2023‑12‑01
  - Filters out tags with < 12 months of data
  - Selects the top 50 tags by total frequency
  - Writes three output artifacts:
      * data/processed/monthly_tag_counts.parquet
      * data/processed/top_50_tags.json
      * data/processed/data_sufficiency_report.json
"""
import json
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RAW_DATA_PATH = Path("data/raw/PostsTags.parquet")
PROCESSED_DIR = Path("data/processed")
MIN_MONTHS_REQUIRED = 12
START_DATE = pd.Timestamp("2015-01-01")
END_DATE = pd.Timestamp("2023-12-31")
TOP_N = 50

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_raw_parquet(parquet_path: Path) -> pd.DataFrame:
    """Load the raw PostsTags parquet file."""
    if not parquet_path.exists():
        raise FileNotFoundError(f"Raw data not found at {parquet_path}")
    log.info(f"Loading raw parquet data from {parquet_path}")
    # The dataset may contain columns with different capitalisation.
    df = pd.read_parquet(parquet_path)
    # Standardise column names to lower‑case for easier handling.
    df.columns = [c.lower() for c in df.columns]
    return df

def _normalize_tags(df: pd.DataFrame) -> pd.DataFrame:
    """Lower‑case and strip whitespace from tag strings."""
    if "tag" not in df.columns:
        raise KeyError("Column 'Tag' (or 'tag') not found in raw data.")
    df = df.copy()
    df["tag"] = df["tag"].astype(str).str.lower().str.strip()
    # Drop empty tags that may appear after stripping.
    df = df[df["tag"] != ""]
    return df

def _parse_creation_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse creation dates and keep rows within the analysis window."""
    # The raw column may be named 'creationdate', 'creation_date', etc.
    date_col_candidates = ["creationdate", "creation_date", "creationdateutc", "creationdateutc"]
    date_col = next((c for c in date_col_candidates if c in df.columns), None)
    if date_col is None:
        raise KeyError("No creation date column found in raw data.")
    df = df.copy()
    df["creation_date"] = pd.to_datetime(df[date_col], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["creation_date"])
    if len(df) < before:
        log.warning(f"Dropped {before - len(df)} rows with unparsable dates.")
    # Restrict to the required period.
    mask = (df["creation_date"] >= START_DATE) & (df["creation_date"] <= END_DATE)
    df = df.loc[mask]
    return df

def _aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate tag counts per month (YYYY‑MM)."""
    df = df.copy()
    df["year_month"] = df["creation_date"].dt.to_period("M").astype(str)
    agg = (
        df.groupby(["tag", "year_month"])
        .size()
        .reset_index(name="count")
        .sort_values(["tag", "year_month"])
    )
    return agg

def _filter_by_data_sufficiency(agg: pd.DataFrame) -> (pd.DataFrame, Dict):
    """
    Keep only tags that appear in at least MIN_MONTHS_REQUIRED distinct months.
    Returns the filtered DataFrame and a report dictionary.
    """
    month_counts = (
        agg.groupby("tag")["year_month"]
        .nunique()
        .reset_index(name="month_count")
    )
    sufficient_tags = month_counts[
        month_counts["month_count"] >= MIN_MONTHS_REQUIRED
    ]["tag"]
    filtered = agg[agg["tag"].isin(sufficient_tags)].copy()

    report = {
        "total_tags_considered": int(month_counts["tag"].nunique()),
        "tags_meeting_min_months": int(sufficient_tags.nunique()),
        "tags_filtered_out": int(
            month_counts["tag"].nunique() - sufficient_tags.nunique()
        ),
        "min_months_required": MIN_MONTHS_REQUIRED,
    }
    return filtered, report

def _select_top_n_tags(agg: pd.DataFrame, n: int) -> List[str]:
    """Select the top `n` tags by total frequency."""
    total_counts = agg.groupby("tag")["count"].sum().reset_index()
    top_tags = (
        total_counts.sort_values("count", ascending=False)
        .head(n)["tag"]
        .tolist()
    )
    return top_tags

def _write_parquet(df: pd.DataFrame, out_path: Path) -> None:
    """Write a DataFrame to Parquet, trying both pyarrow and fastparquet."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(out_path, index=False, engine="pyarrow")
    except Exception as e_py:
        log.warning(f"pyarrow write failed ({e_py}); trying fastparquet.")
        try:
            df.to_parquet(out_path, index=False, engine="fastparquet")
        except Exception as e_fp:
            log.error(
                f"Both pyarrow and fastparquet failed to write Parquet: {e_fp}"
            )
            raise RuntimeError(
                "Unable to write Parquet file with available engines."
            ) from e_fp

def _write_json(obj: object, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def main() -> int:
    """
    Execute the preprocessing pipeline.

    Returns
    -------
    int
        0 on success, non‑zero on failure.
    """
    log.info("Starting preprocessing of Stack Overflow PostsTags data (T009).")
    try:
        # 1. Load raw parquet
        raw_df = _load_raw_parquet(RAW_DATA_PATH)

        # 2. Normalise tags
        raw_df = _normalize_tags(raw_df)

        # 3. Parse dates and restrict to analysis window
        raw_df = _parse_creation_dates(raw_df)

        # 4. Aggregate monthly frequencies
        monthly_df = _aggregate_monthly(raw_df)

        # 5. Filter tags with insufficient month coverage
        monthly_df, sufficiency_report = _filter_by_data_sufficiency(monthly_df)

        # 6. Determine top‑50 tags
        top_50_tags = _select_top_n_tags(monthly_df, TOP_N)

        # 7. Write outputs
        monthly_parquet_path = paths.data("processed", "monthly_tag_counts.parquet")
        _write_parquet(monthly_df, monthly_parquet_path)

        top_tags_path = paths.data("processed", "top_50_tags.json")
        _write_json(top_50_tags, top_tags_path)

        sufficiency_path = paths.data(
            "processed", "data_sufficiency_report.json"
        )
        _write_json(sufficiency_report, sufficiency_path)

        log.info("Preprocessing completed successfully.")
        log.info(f"Written monthly counts to {monthly_parquet_path}")
        log.info(f"Written top‑50 tags to {top_tags_path}")
        log.info(f"Written data‑sufficiency report to {sufficiency_path}")
        return 0

    except Exception as exc:
        log.error(f"Preprocessing failed: {exc}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys

    sys.exit(main())
