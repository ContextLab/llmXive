"""
Timestamp simulation module for the evaluation pipeline.

This placeholder reads ``merged_features.parquet`` (if present) and
adds three timestamp‑related columns, writing the result to
``merged_features_with_timestamps.parquet``.
"""

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """
    Append placeholder timestamp columns to the merged features file.
    """
    input_path = paths.data("processed", "merged_features.parquet")
    output_path = paths.data("processed", "merged_features_with_timestamps.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        log.warning(f"Could not read merged features: {e}")
        df = pd.DataFrame()

    # Add placeholder timestamp columns
    df["created_at"] = pd.NaT
    df["review_effort_duration"] = pd.NA
    df["total_review_duration"] = pd.NA

    df.to_parquet(output_path, index=False)
    log.info(f"Merged features with timestamps written to {output_path}")
