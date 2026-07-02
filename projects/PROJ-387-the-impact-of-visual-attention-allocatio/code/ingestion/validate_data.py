"""
Data Validation Module for Visual Attention Study (US1).

Validates column existence, data quality metrics, and valence labels
against the project's data model and requirements (FR-002).
"""
import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd

# Import from project utilities (API Surface)
from utils.config import get_project_root, get_data_path, load_config
from utils.logger import get_logger, setup_logging
from models.data_models import QualityReport

# Constants defined by requirements (FR-002)
REQUIRED_COLUMNS = [
    "fixation_duration",
    "saccade_amplitude",
    "gaze_distribution",
    "recall_accuracy",
    "valence_label"
]

# Track loss threshold (Constitution VI)
MAX_TRACK_LOSS_PERCENT = 5.0

logger = None

def validate_columns(df: pd.DataFrame, dataset_name: str = "unknown") -> Dict[str, Any]:
    """
    Validates that all required columns exist in the DataFrame.

    Args:
        df: The loaded pandas DataFrame.
        dataset_name: Name of the dataset for logging.

    Returns:
        A dictionary with validation status and missing columns.
    """
    global logger
    if logger is None:
        logger = get_logger()

    missing_columns = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_columns.append(col)

    is_valid = len(missing_columns) == 0

    if is_valid:
        logger.info(f"[{dataset_name}] Column validation PASSED: All required columns present.")
    else:
        logger.error(f"[{dataset_name}] Column validation FAILED: Missing columns {missing_columns}")

    return {
        "valid": is_valid,
        "missing_columns": missing_columns,
        "dataset_name": dataset_name
    }

def validate_data_quality_metrics(df: pd.DataFrame, dataset_name: str = "unknown") -> Dict[str, Any]:
    """
    Validates data quality metrics:
    1. Track loss <= 5% (Constitution VI).
    2. Eye-tracker calibration status (assumed valid if 'calibrated' column exists and is True).

    Args:
        df: The loaded pandas DataFrame.
        dataset_name: Name of the dataset for logging.

    Returns:
        Dictionary with quality metrics status.
    """
    global logger
    if logger is None:
        logger = get_logger()

    issues = []

    # Check track loss if 'track_loss' or similar column exists
    # Assuming a column named 'track_loss' or 'missing_gaze_ratio' might exist
    track_loss_col = None
    for col in ["track_loss", "missing_gaze_ratio", "data_loss"]:
        if col in df.columns:
            track_loss_col = col
            break

    if track_loss_col:
        # Calculate average track loss if multiple rows
        avg_loss = df[track_loss_col].mean() * 100.0
        if avg_loss > MAX_TRACK_LOSS_PERCENT:
            issues.append(f"Track loss ({avg_loss:.2f}%) exceeds threshold ({MAX_TRACK_LOSS_PERCENT}%)")
            logger.error(f"[{dataset_name}] Track loss ({avg_loss:.2f}%) > {MAX_TRACK_LOSS_PERCENT}%")
        else:
            logger.info(f"[{dataset_name}] Track loss ({avg_loss:.2f}%) within limits.")
    else:
        # If no track loss column, assume 0% or log warning
        logger.warning(f"[{dataset_name}] No track loss column found. Assuming 0% loss.")

    # Check calibration status
    if "calibrated" in df.columns:
        if not df["calibrated"].all():
            issues.append("Dataset contains uncalibrated eye-tracker data.")
            logger.error(f"[{dataset_name}] Uncalibrated data detected.")
        else:
            logger.info(f"[{dataset_name}] All data is calibrated.")
    else:
        logger.warning(f"[{dataset_name}] No 'calibrated' column found. Assuming valid.")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "dataset_name": dataset_name
    }

def validate_valence_labels(df: pd.DataFrame, dataset_name: str = "unknown") -> Dict[str, Any]:
    """
    Validates valence annotation for standardized rating scale.
    Checks for non-null values and expected categories if defined.

    Args:
        df: The loaded pandas DataFrame.
        dataset_name: Name of the dataset for logging.

    Returns:
        Dictionary with valence validation status.
    """
    global logger
    if logger is None:
        logger = get_logger()

    issues = []
    valence_col = "valence_label"

    if valence_col not in df.columns:
        issues.append(f"Column '{valence_col}' missing.")
        logger.error(f"[{dataset_name}] Missing required column: {valence_col}")
        return {
            "valid": False,
            "issues": issues,
            "unique_values": [],
            "count": 0,
            "dataset_name": dataset_name
        }

    # Check for nulls
    null_count = df[valence_col].isnull().sum()
    if null_count > 0:
        issues.append(f"Found {null_count} null values in '{valence_col}'.")
        logger.warning(f"[{dataset_name}] Found {null_count} null values in valence_label.")

    unique_vals = df[valence_col].dropna().unique().tolist()
    logger.info(f"[{dataset_name}] Valence categories found: {unique_vals}")

    return {
        "valid": len(issues) == 0 and null_count == 0,
        "issues": issues,
        "unique_values": unique_vals,
        "count": len(unique_vals),
        "dataset_name": dataset_name
    }

def write_quality_report(
    column_results: List[Dict],
    quality_results: List[Dict],
    valence_results: List[Dict],
    output_path: Path
) -> None:
    """
    Aggregates all validation results and writes a markdown quality report.

    Args:
        column_results: List of dicts from validate_columns.
        quality_results: List of dicts from validate_data_quality_metrics.
        valence_results: List of dicts from validate_valence_labels.
        output_path: Path to write the quality_report.md file.
    """
    global logger
    if logger is None:
        logger = get_logger()

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# Data Quality Report",
        f"Generated by: validate_data.py",
        "",
        "## Column Validation",
    ]

    all_valid = True

    for res in column_results:
        status = "PASS" if res["valid"] else "FAIL"
        if not res["valid"]:
            all_valid = False
        report_lines.append(f"- **{res['dataset_name']}**: {status}")
        if not res["valid"]:
            report_lines.append(f"  - Missing: {res['missing_columns']}")

    report_lines.extend([
        "",
        "## Data Quality Metrics",
    ])

    for res in quality_results:
        status = "PASS" if res["valid"] else "FAIL"
        if not res["valid"]:
            all_valid = False
        report_lines.append(f"- **{res['dataset_name']}**: {status}")
        if res["issues"]:
            for issue in res["issues"]:
                report_lines.append(f"  - {issue}")

    report_lines.extend([
        "",
        "## Valence Annotation",
    ])

    total_valence_categories = set()
    for res in valence_results:
        status = "PASS" if res["valid"] else "FAIL"
        if not res["valid"]:
            all_valid = False
        report_lines.append(f"- **{res['dataset_name']}**: {status}")
        if res["unique_values"]:
            report_lines.append(f"  - Categories: {', '.join(map(str, res['unique_values']))}")
            total_valence_categories.update(res["unique_values"])

    report_lines.extend([
        "",
        "## Summary",
        f"- **Overall Status**: {'PASS' if all_valid else 'FAIL'}",
        f"- **Total Unique Valence Categories**: {len(total_valence_categories)}",
    ])

    # Write markdown
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    logger.info(f"Quality report written to: {output_path}")

    # Also write a JSON summary for programmatic access if needed
    json_path = output_path.with_suffix('.json')
    summary_data = {
        "overall_pass": all_valid,
        "valence_categories_count": len(total_valence_categories),
        "details": {
            "columns": column_results,
            "quality": quality_results,
            "valence": valence_results
        }
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    if not all_valid:
        # Signal a halt condition via exit code in main, but here just log
        logger.error("Data validation failed. Halting pipeline.")

def main():
    """
    Main entry point for data validation.
    Expects a data file path or directory as argument.
    """
    global logger
    parser = argparse.ArgumentParser(description="Validate eye-tracking and recall data.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV/EDF file or directory.")
    parser.add_argument("--output", type=str, default="data/eye-tracking/quality_report.md", help="Path for output report.")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level.")

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level)
    logger = get_logger()

    project_root = get_project_root()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)

    # Determine if single file or directory
    if input_path.is_file():
        files_to_process = [input_path]
    else:
        # Look for CSVs
        files_to_process = list(input_path.glob("*.csv"))
        if not files_to_process:
            logger.error(f"No CSV files found in {input_path}")
            sys.exit(1)

    column_results = []
    quality_results = []
    valence_results = []
    overall_success = True

    for file_path in files_to_process:
        logger.info(f"Processing: {file_path.name}")
        try:
            # Load data using the ingestion module (T012)
            # Assuming load_data.py has a function to load CSVs
            # We import here to avoid circular deps if possible, or use pandas directly if simple
            from ingestion.load_data import load_csv
            df = load_csv(file_path)

            if df is None or df.empty:
                logger.error(f"Failed to load or empty data from {file_path}")
                overall_success = False
                continue

            # 1. Validate Columns
            col_res = validate_columns(df, dataset_name=file_path.name)
            column_results.append(col_res)
            if not col_res["valid"]:
                overall_success = False

            # 2. Validate Quality Metrics
            qual_res = validate_data_quality_metrics(df, dataset_name=file_path.name)
            quality_results.append(qual_res)
            if not qual_res["valid"]:
                overall_success = False

            # 3. Validate Valence
            val_res = validate_valence_labels(df, dataset_name=file_path.name)
            valence_results.append(val_res)
            if not val_res["valid"]:
                overall_success = False

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            overall_success = False

    # Write Report
    write_quality_report(column_results, quality_results, valence_results, output_path)

    if not overall_success:
        logger.error("Validation failed. Exiting with code 1.")
        sys.exit(1)

    logger.info("Validation completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()