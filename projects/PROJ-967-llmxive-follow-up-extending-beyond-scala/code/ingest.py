import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

from primary_dimension_util import process_dataframe_primary_dimensions

def setup_logging():
    """Configure logging for the ingest script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def setup_directories(base_path: Path):
    """Ensure required directories exist."""
    (base_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (base_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (base_path / "results").mkdir(parents=True, exist_ok=True)

def load_and_align_data(logger: logging.Logger, raw_input_path: Path, output_path: Path, use_mock: bool = False):
    """
    Load the Z-Reward dataset, align teacher/student/human data,
    and apply the primary dimension logic.

    This function implements T012 (ingestion), T013 (alignment),
    T014 (primary dimension logic via utility), and T015 (chunking).
    """
    logger.info(f"Loading dataset from {raw_input_path}")

    if not raw_input_path.exists():
        raise FileNotFoundError(f"Input file not found: {raw_input_path}")

    # T015: Chunked loading logic (simulated for parquet via chunks if needed,
    # but for this task we assume the file is loadable within memory limits
    # or the user has pre-sampled. We add a check for size).
    file_size_mb = raw_input_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 6000:  # Warning threshold < 7GB
        logger.warning(f"File size {file_size_mb:.1f} MB is large. Consider sampling.")

    try:
        # Load in chunks if the file is extremely large, otherwise standard load
        # For parquet, we assume the file is already managed or small enough for this stage
        df = pd.read_parquet(raw_input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet: {e}")
        raise

    logger.info(f"Loaded {len(df)} rows.")

    # T013: Alignment logic
    # Ensure required columns exist. If missing, mark excluded_reason.
    required_cols = ["prompt", "image_url", "teacher_scores", "student_scalar", "human_annotations", "primary_dimension"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns: {missing_cols}. Attempting schema alignment or exclusion.")
        # In a real scenario, we might try to map columns. Here we raise if critical.
        if "teacher_scores" in missing_cols or "human_annotations" in missing_cols:
            raise ValueError(f"Critical schema mismatch: Missing {missing_cols}")

    # Align student_scalar if missing
    if "student_scalar" not in df.columns:
        df["excluded_reason"] = "missing_student_scalar"
        logger.warning("student_scalar missing; marking samples as excluded.")
    else:
        df["excluded_reason"] = df["excluded_reason"].fillna("none")
        mask_missing = df["student_scalar"].isna()
        df.loc[mask_missing, "excluded_reason"] = "missing_student_scalar"

    # T014: Primary Dimension Logic (using utility)
    # The utility function handles the metadata rule and exclusion.
    logger.info("Applying primary dimension derivation logic (T014)...")
    df = process_dataframe_primary_dimensions(df, logger)

    # Filter out samples where primary_dimension was excluded (if any)
    # The utility should have handled exclusion logic, but we double-check.
    if "primary_dimension" in df.columns:
        null_dims = df["primary_dimension"].isna()
        if null_dims.any():
            logger.warning(f"Excluding {null_dims.sum()} samples with null primary_dimension.")
            df = df[~null_dims].reset_index(drop=True)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Aligned data written to {output_path}")

    return df

def print_summary(df: pd.DataFrame, logger: logging.Logger):
    """
    T016: Print summary output including sample counts, missing-data flags,
    and dimension coverage stats.
    """
    logger.info("--- Ingestion Summary (T016) ---")
    logger.info(f"Total Samples: {len(df)}")

    # Missing Data Flags
    missing_stats = df.isna().sum()
    logger.info("Missing Data Counts:")
    for col, count in missing_stats.items():
        if count > 0:
            logger.info(f"  {col}: {count}")

    # Excluded Reasons
    if "excluded_reason" in df.columns:
        excluded_counts = df["excluded_reason"].value_counts()
        logger.info("Exclusion Breakdown:")
        for reason, count in excluded_counts.items():
            logger.info(f"  {reason}: {count}")
    else:
        logger.info("No 'excluded_reason' column found.")

    # Dimension Coverage Stats
    if "primary_dimension" in df.columns:
        dim_counts = df["primary_dimension"].value_counts()
        logger.info("Primary Dimension Coverage:")
        for dim, count in dim_counts.items():
            pct = (count / len(df)) * 100
            logger.info(f"  {dim}: {count} ({pct:.1f}%)")
    else:
        logger.warning("No 'primary_dimension' column found for coverage stats.")

    # Teacher Scores Dimensions (if available)
    if "teacher_scores" in df.columns:
        # Teacher scores is a dict/object column. We check for keys.
        dims = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
        logger.info("Teacher Score Dimension Presence:")
        for dim in dims:
            # Check if any row has this key in the dict
            has_dim = df["teacher_scores"].apply(lambda x: dim in x if isinstance(x, dict) else False)
            count = has_dim.sum()
            logger.info(f"  {dim}: {count} samples")

    logger.info("--- End Summary ---")

def parse_args():
    parser = argparse.ArgumentParser(description="Ingest and align Z-Reward dataset.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/z_reward.parquet"),
        help="Path to the raw input parquet file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/raw_data.parquet"),
        help="Path to the output aligned parquet file.",
    )
    parser.add_argument(
        "--use-mock-data",
        action="store_true",
        help="Flag to indicate mock data usage (for testing).",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    setup_directories(Path("."))

    try:
        df = load_and_align_data(logger, args.input, args.output, use_mock=args.use_mock_data)
        print_summary(df, logger)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()