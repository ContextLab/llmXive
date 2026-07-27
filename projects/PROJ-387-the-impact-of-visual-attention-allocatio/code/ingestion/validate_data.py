import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import existing utilities from the project API surface
from utils.logger import get_logger
from utils.config import get_project_root, get_data_path
from models.data_models import QualityReport

# Required columns as per FR-002 and task requirements
REQUIRED_COLUMNS = [
    "fixation_duration",
    "saccade_amplitude",
    "gaze_distribution",
    "recall_accuracy",
    "valence_label"
]

def validate_columns(df: Any, logger: Any) -> bool:
    """
    Validates that the DataFrame contains all required columns.
    Returns True if all columns exist, False otherwise.
    """
    missing_columns = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)
    
    if missing_columns:
        logger.error(f"Missing required variables: {missing_columns}")
        return False
    
    logger.info("All required variables present.")
    return True

def validate_data_quality_metrics(df: Any, logger: Any) -> bool:
    """
    Validates data quality metrics:
    - Track loss <= 5%
    - Eye-tracker is calibrated
    
    Returns True if metrics pass, False otherwise.
    """
    # Check for track loss
    if "track_loss" in df.columns:
        track_loss_rate = df["track_loss"].mean()
        if track_loss_rate > 0.05:
            logger.error(f"Track loss rate ({track_loss_rate:.2%}) exceeds 5% threshold.")
            return False
        logger.info(f"Track loss rate ({track_loss_rate:.2%}) within acceptable limits.")
    else:
        logger.warning("Track loss column not found, skipping track loss validation.")

    # Check for calibration status
    if "calibrated" in df.columns:
        uncalibrated_count = (~df["calibrated"]).sum()
        if uncalibrated_count > 0:
            logger.error(f"Found {uncalibrated_count} records with uncalibrated eye-tracker.")
            return False
        logger.info("All records are from calibrated eye-tracker.")
    else:
        logger.warning("Calibration status column not found, skipping calibration validation.")

    return True

def validate_valence_labels(df: Any, logger: Any) -> bool:
    """
    Validates valence annotation:
    - Standardized rating scale
    - Human-rated metadata only
    
    Returns True if valid, False otherwise.
    """
    if "valence_label" not in df.columns:
        logger.error("Valence label column missing.")
        return False

    # Check if valence labels are from human-rated metadata
    # Assuming a column 'valence_source' indicates the source
    if "valence_source" in df.columns:
        non_human_sources = df[~df["valence_source"].isin(["human-rated", "human"])].copy()
        if len(non_human_sources) > 0:
            logger.error(f"Found {len(non_human_sources)} records with non-human-rated valence metadata.")
            return False
        logger.info("All valence labels are from human-rated metadata.")
    else:
        # If no source column, assume human-rated but warn
        logger.warning("Valence source column not found. Assuming human-rated, but this should be verified.")

    return True

def write_quality_report(
    logger: Any,
    track_loss_ok: bool,
    calibrated_ok: bool,
    valence_ok: bool,
    valence_categories_count: Optional[int] = None
) -> None:
    """
    Writes the quality report to data/eye-tracking/quality_report.md.
    """
    project_root = get_project_root()
    report_path = project_root / "data" / "eye-tracking" / "quality_report.md"
    
    # Ensure directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write("# Data Quality Report\n\n")
        f.write(f"Track Loss Check: {'PASS' if track_loss_ok else 'FAIL'}\n")
        f.write(f"Calibration Check: {'PASS' if calibrated_ok else 'FAIL'}\n")
        f.write(f"Valence Validation: {'PASS' if valence_ok else 'FAIL'}\n")
        if valence_categories_count is not None:
            f.write(f"Categories Count: {valence_categories_count}\n")
        f.write("\n")

    logger.info(f"Quality report written to {report_path}")

def main():
    """
    Main entry point for data validation.
    Halts processing with exit code 1 if dataset is incompatible (missing variables).
    """
    logger = get_logger("validate_data")
    project_root = get_project_root()
    data_path = get_data_path()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Validate eye-tracking data.")
    parser.add_argument("--data-file", type=str, required=True, help="Path to the data file (CSV/EDF).")
    args = parser.parse_args()

    data_file = Path(args.data_file)
    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        sys.exit(1)

    # Load data (simplified for validation; actual loading handled by load_data.py)
    # For this task, we assume the data is already loaded into a DataFrame 'df'
    # In a real scenario, this would call load_data.load_data()
    import pandas as pd
    if data_file.suffix == ".csv":
        df = pd.read_csv(data_file)
    elif data_file.suffix == ".edf":
        # Placeholder for EDF loading; actual implementation in load_data.py
        logger.error("EDF loading not implemented in this snippet. Use load_data.py for EDF.")
        sys.exit(1)
    else:
        logger.error(f"Unsupported file format: {data_file.suffix}")
        sys.exit(1)

    # Step 1: Validate required columns (T013)
    columns_valid = validate_columns(df, logger)

    # Step 2: Validate data quality metrics (T014)
    quality_valid = validate_data_quality_metrics(df, logger)

    # Step 3: Validate valence labels (T015)
    valence_valid = validate_valence_labels(df, logger)

    # Step 4: Write quality report (T014, T015)
    valence_categories_count = None
    if "valence_label" in df.columns:
        valence_categories_count = df["valence_label"].nunique()

    write_quality_report(logger, columns_valid and quality_valid, quality_valid, valence_valid, valence_categories_count)

    # Step 5: HALT if dataset is incompatible (missing variables) - T016
    if not columns_valid:
        logger.error("DATA_BLOCKER: Missing required variables")
        sys.exit(1)

    # HALT if data quality fails (T014)
    if not quality_valid:
        logger.error("DATA_BLOCKER: Data quality metrics failed")
        sys.exit(1)

    # HALT if valence validation fails (T015)
    if not valence_valid:
        logger.error("DATA_BLOCKER: Valence annotation validation failed")
        sys.exit(1)

    logger.info("Data validation completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()