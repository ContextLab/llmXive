"""
Participant Exclusion Logic for Visual Search Dataset.

Implements exclusion criteria based on missing gaze data.
Excludes participants with >20% missing gaze data.
Logs exclusion rate and writes exclusion report.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Import from project API
from utils.logging import get_logger
from config import get_config


def get_logger_wrapper(logger_name: str = "exclusion") -> logging.Logger:
    """Get a logger configured for the exclusion module."""
    return get_logger(logger_name)


def calculate_missing_ratio(gaze_data: pd.Series) -> float:
    """
    Calculate the ratio of missing gaze data points.

    Args:
        gaze_data: Series of gaze coordinates or fixation data.

    Returns:
        Float between 0.0 and 1.0 representing the missing ratio.
    """
    if gaze_data is None or len(gaze_data) == 0:
        return 1.0

    # Count non-null and valid entries
    valid_count = gaze_data.notna().sum()
    total_count = len(gaze_data)

    if total_count == 0:
        return 1.0

    missing_count = total_count - valid_count
    return missing_count / total_count


def evaluate_participant_exclusion(
    participant_data: pd.DataFrame,
    threshold: float = 0.20,
    gaze_column: str = "gaze_coordinates"
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Evaluate if a participant should be excluded based on missing gaze data.

    Args:
        participant_data: DataFrame containing participant's raw data.
        threshold: Maximum allowed missing ratio (default 0.20 = 20%).
        gaze_column: Name of the column containing gaze data.

    Returns:
        Tuple of (should_exclude, missing_ratio, details_dict)
    """
    if gaze_column not in participant_data.columns:
        # If column missing, treat as 100% missing
        return True, 1.0, {
            "reason": f"Missing required column: {gaze_column}",
            "gaze_column": gaze_column
        }

    # Handle case where gaze data might be a list of dicts or nested structure
    gaze_series = participant_data[gaze_column]

    # Calculate missing ratio
    missing_ratio = calculate_missing_ratio(gaze_series)

    should_exclude = missing_ratio > threshold

    details = {
        "participant_id": participant_data.get("participant_id", "unknown"),
        "total_records": len(participant_data),
        "missing_ratio": missing_ratio,
        "threshold": threshold,
        "excluded": should_exclude,
        "reason": "Missing gaze data exceeds threshold" if should_exclude else None
    }

    return should_exclude, missing_ratio, details


def run_exclusion_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    threshold: float = 0.20,
    gaze_column: str = "gaze_coordinates"
) -> Dict[str, Any]:
    """
    Run the full exclusion pipeline on a dataset.

    Args:
        input_path: Path to input CSV/Parquet file with raw data.
        output_path: Path to save cleaned data (excluded participants removed).
        threshold: Exclusion threshold (default 0.20).
        gaze_column: Column name containing gaze data.

    Returns:
        Dictionary containing exclusion statistics and report.
    """
    logger = get_logger_wrapper()
    config = get_config()

    # Default paths if not provided
    if input_path is None:
        input_path = str(config.DATA_PROCESSED_PATH / "features.csv")
    if output_path is None:
        output_path = str(config.DATA_PROCESSED_PATH / "features_cleaned.csv")

    logger.info(f"Starting exclusion pipeline with threshold: {threshold}")
    logger.info(f"Input file: {input_path}")

    # Load data
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")

    # Ensure participant_id column exists
    if "participant_id" not in df.columns:
        logger.warning("No participant_id column found. Attempting to infer...")
        # If no participant_id, assume each row is a unique participant trial
        # In this case, we might need to group by other identifiers or skip
        # For now, we'll create a temporary ID if needed
        if "trial_id" in df.columns:
            df["participant_id"] = df["trial_id"].apply(lambda x: f"trial_{x}")
        else:
            df["participant_id"] = [f"p_{i}" for i in range(len(df))]
            logger.warning("Created synthetic participant_id based on row index.")

    # Group by participant_id to evaluate exclusion per participant
    grouped = df.groupby("participant_id")

    exclusion_results = []
    included_participants = []
    excluded_participants = []

    for pid, group in grouped:
        should_exclude, missing_ratio, details = evaluate_participant_exclusion(
            group,
            threshold=threshold,
            gaze_column=gaze_column
        )

        details["participant_id"] = pid
        exclusion_results.append(details)

        if should_exclude:
            excluded_participants.append(pid)
            logger.warning(
                f"Excluding participant {pid}: missing_ratio={missing_ratio:.2%} "
                f"(threshold={threshold:.2%})"
            )
        else:
            included_participants.append(pid)

    # Create exclusion report
    total_participants = len(grouped)
    excluded_count = len(excluded_participants)
    included_count = len(included_participants)
    exclusion_rate = excluded_count / total_participants if total_participants > 0 else 0.0

    report = {
        "total_participants": total_participants,
        "excluded_count": excluded_count,
        "included_count": included_count,
        "exclusion_rate": exclusion_rate,
        "threshold": threshold,
        "gaze_column": gaze_column,
        "excluded_participants": excluded_participants,
        "included_participants": included_participants,
        "details": exclusion_results
    }

    # Log summary
    logger.info("=" * 60)
    logger.info("EXCLUSION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total participants: {total_participants}")
    logger.info(f"Excluded: {excluded_count} ({exclusion_rate:.2%})")
    logger.info(f"Included: {included_count} ({1 - exclusion_rate:.2%})")
    logger.info(f"Threshold: {threshold:.2%}")
    logger.info("=" * 60)

    # Save cleaned data if there are included participants
    if included_count > 0:
        cleaned_df = df[df["participant_id"].isin(included_participants)]
        cleaned_df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to: {output_path}")
        logger.info(f"Cleaned dataset contains {len(cleaned_df)} records from {included_count} participants")
    else:
        logger.error("No participants passed the exclusion criteria. Output file not created.")

    # Save exclusion report
    report_path = config.DATA_PROCESSED_PATH / "exclusion_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Exclusion report saved to: {report_path}")

    return report


def main():
    """Main entry point for the exclusion pipeline."""
    config = get_config()
    logger = get_logger_wrapper()

    # Ensure output directories exist
    config.DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    try:
        # Run exclusion pipeline
        report = run_exclusion_pipeline(
            input_path=str(config.DATA_PROCESSED_PATH / "features.csv"),
            output_path=str(config.DATA_PROCESSED_PATH / "features_cleaned.csv"),
            threshold=0.20,
            gaze_column="gaze_coordinates"
        )

        logger.info("Exclusion pipeline completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Exclusion pipeline failed: {e}")
        raise


if __name__ == "__main__":
    sys.exit(main())
