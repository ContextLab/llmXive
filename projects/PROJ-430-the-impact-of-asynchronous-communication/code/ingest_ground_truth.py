"""
Ingest external human-annotated ground truth data for cohesion validation.

This script loads the manual ground truth CSV from data/validation/manual_ground_truth.csv,
validates its schema, and logs the ingestion statistics.

Required columns: project_id, comment_id, manual_cohesion_score
"""
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

from config import get_config, ensure_directories_exist
from utils.logger import get_logger

REQUIRED_COLUMNS = {"project_id", "comment_id", "manual_cohesion_score"}

def load_ground_truth(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the manual ground truth CSV from disk.

    Args:
        path: Optional path to the CSV file. If None, uses the configured path.

    Returns:
        DataFrame containing the ground truth data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the schema is invalid.
    """
    config = get_config()
    if path is None:
        path = config["paths"]["validation_dir"] / "manual_ground_truth.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Ground truth file not found at {path}. "
            "Ensure the external human annotation CSV has been placed here."
        )

    df = pd.read_csv(path)

    # Validate schema
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Ground truth CSV is missing required columns: {missing_cols}. "
            f"Required columns: {REQUIRED_COLUMNS}"
        )

    # Validate data types and basic constraints
    if df["manual_cohesion_score"].isna().any():
        logging.warning("Ground truth contains NaN values in manual_cohesion_score column.")
    
    if (df["manual_cohesion_score"] < 0).any() or (df["manual_cohesion_score"] > 1).any():
        logging.warning("Some manual_cohesion_score values are outside the expected [0, 1] range.")

    return df

def log_ingestion_stats(df: pd.DataFrame, logger: logging.Logger) -> None:
    """Log statistics about the ingested ground truth data."""
    total_rows = len(df)
    unique_projects = df["project_id"].nunique()
    unique_comments = df["comment_id"].nunique()
    score_mean = df["manual_cohesion_score"].mean()
    score_std = df["manual_cohesion_score"].std()

    logger.info(f"Ground truth ingestion complete.")
    logger.info(f"  Total records: {total_rows}")
    logger.info(f"  Unique projects: {unique_projects}")
    logger.info(f"  Unique comments: {unique_comments}")
    logger.info(f"  Score mean: {score_mean:.4f}")
    logger.info(f"  Score std: {score_std:.4f}")

def run_ingest_ground_truth(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Main entry point for the ground truth ingestion pipeline.

    Args:
        output_path: Optional path to save a cleaned/validated version of the data.
                    If None, the original file is not modified.

    Returns:
        The loaded and validated DataFrame.
    """
    logger = get_logger(__name__)
    logger.info("Starting ground truth ingestion pipeline.")

    try:
        df = load_ground_truth(output_path)
        log_ingestion_stats(df, logger)

        # Ensure directories exist if we are writing output
        if output_path:
            ensure_directories_exist([output_path.parent])
            df.to_csv(output_path, index=False)
            logger.info(f"Saved validated ground truth to {output_path}")

        logger.info("Ground truth ingestion pipeline completed successfully.")
        return df

    except FileNotFoundError as e:
        logger.error(f"Failed to load ground truth: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during ground truth ingestion: {e}")
        raise

def main() -> None:
    """CLI entry point."""
    config = get_config()
    ground_truth_path = config["paths"]["validation_dir"] / "manual_ground_truth.csv"
    run_ingest_ground_truth(ground_truth_path)

if __name__ == "__main__":
    main()