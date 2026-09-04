"""
Script to filter alloy dataset rows based on label source and confidence.
Specifically marks rows with DFT-derived labels as low confidence and
sets the `experimental_validation_status` based on XRD availability.

Output:
    data/derived/filtered_alloys.csv
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/filter_labels.log"),
    ],
)
logger = logging.getLogger(__name__)


def load_data(input_path: str) -> pd.DataFrame:
    """Load the alloy dataset from a CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    logger.info(f"Loading data from {input_path}")
    return pd.read_csv(input_path)


def determine_validation_status(row: pd.Series) -> str:
    """
    Determine the `experimental_validation_status` based on XRD flag.

    Logic:
    - If 'has_xrd' (or similar flag) is True and source is experimental: 'yes'
    - If source is experimental but XRD is missing/False: 'no'
    - If source is DFT or unknown: 'unknown'
    - Default fallback: 'unknown'

    Assumption: The input CSV contains columns:
    - 'phase_label' or 'label_source' indicating the origin (e.g., 'experimental', 'dft')
    - 'has_xrd' (boolean) or 'xrd_available' indicating XRD data presence.
      If these columns do not exist, we assume XRD is missing.
    """
    source = str(row.get("label_source", row.get("source", "unknown"))).lower()
    has_xrd = False

    # Check for XRD flag
    for col in ["has_xrd", "xrd_available", "xrd_present"]:
        if col in row.index:
            val = row[col]
            if isinstance(val, bool):
                has_xrd = val
            elif isinstance(val, str):
                has_xrd = val.lower() in ("true", "1", "yes")
            break

    if source in ("experimental", "experiment"):
        if has_xrd:
            return "yes"
        else:
            return "no"
    else:
        # DFT, theoretical, or unknown source
        return "unknown"


def filter_and_update_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter rows based on label source (retain experimental, mark DFT as low confidence)
    and set `experimental_validation_status`.

    Returns:
        DataFrame with updated columns and potentially filtered rows (if strict filtering is desired).
        Currently, we retain all rows but update confidence and status.
    """
    logger.info("Filtering labels and updating validation status...")

    # Ensure 'confidence' column exists
    if "confidence" not in df.columns:
        df["confidence"] = "high"

    # Update confidence for DFT-derived rows
    dft_mask = df["label_source"].str.lower().isin(["dft", "theoretical", "simulation"])
    df.loc[dft_mask, "confidence"] = "low"
    if dft_mask.any():
        logger.warning(f"Marked {dft_mask.sum()} rows as 'low' confidence (DFT-derived).")

    # Determine experimental_validation_status for every row
    df["experimental_validation_status"] = df.apply(determine_validation_status, axis=1)

    # Log distribution of validation status
    status_counts = df["experimental_validation_status"].value_counts()
    logger.info("Validation status distribution:\n%s", status_counts.to_string())

    return df


def save_data(df: pd.DataFrame, output_path: str) -> None:
    """Save the processed DataFrame to a CSV file."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    logger.info(f"Saving filtered data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Data saved successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Filter alloy labels and set experimental validation status."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/alloy_dataset.csv",
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/filtered_alloys.csv",
        help="Path to the output CSV file.",
    )
    args = parser.parse_args()

    try:
        df = load_data(args.input)
        df_filtered = filter_and_update_labels(df)
        save_data(df_filtered, args.output)
        logger.info("Task completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()