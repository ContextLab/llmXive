"""
I/O utilities for correlation analysis results.
Handles saving correlation results to CSV with strict schema validation.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from src.config import load_config

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "sample_id",
    "diversity_index",
    "sleep_metric",
    "r",
    "p",
    "q",
    "is_moderate",
    "is_significant",
    "status"
]

def save_correlation_results(
    df: pd.DataFrame,
    output_path: Optional[str] = None
) -> None:
    """
    Save correlation analysis results to a CSV file.

    Args:
        df: DataFrame containing correlation results with required columns.
        output_path: Optional path to output file. Defaults to config value.

    Raises:
        ValueError: If required columns are missing or DataFrame is empty
                   (unless status indicates blocked).
        FileNotFoundError: If output directory does not exist.
    """
    config = load_config()
    if output_path is None:
        output_path = config.get("OUTPUT_CORRELATION_PATH", "data/processed/correlation_results.csv")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Validate DataFrame structure
    if df.empty:
        # Check if this is a blocked state
        if "status" in df.columns and any(df["status"] == "blocked"):
            logger.warning("Saving blocked correlation results (empty DataFrame with status=blocked)")
        else:
            raise ValueError(
                "Correlation results DataFrame is empty and does not indicate a blocked state. "
                "Cannot save empty results without explicit blocked status."
            )

    # Ensure all required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Correlation results missing required columns: {missing_cols}. "
            f"Required: {REQUIRED_COLUMNS}"
        )

    # Validate data types for numeric columns
    for col in ["r", "p", "q"]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Validate boolean columns
    for col in ["is_moderate", "is_significant"]:
        if col in df.columns and not pd.api.types.is_bool_dtype(df[col]):
            df[col] = df[col].astype(bool)

    # Ensure sample_id is string
    if "sample_id" in df.columns:
        df["sample_id"] = df["sample_id"].astype(str)

    # Write to CSV
    df.to_csv(output_file, index=False)
    logger.info(f"Saved correlation results to {output_file} ({len(df)} rows)")

    # Verify file was written
    if not output_file.exists():
        raise RuntimeError(f"Failed to write correlation results to {output_file}")

    logger.info(f"Verified file existence: {output_file.stat().st_size} bytes")
