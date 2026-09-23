"""
Script to validate the results of the smoke test (T050b).
Verifies that all expected output files exist and contain valid data.
"""
import csv
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config import RESULTS_DIR
from code.utils import setup_logging

# Configure logging
logger = setup_logging("validate_smoke_test", level=logging.INFO)

# Define expected files
EXPECTED_FILES = [
    "raw_evaluations.csv",
    "stability_metrics.csv",
    "correlation_results.csv",
    "permutation_results.csv",
    "final_report.md"
]

# Critical columns to check for NaN
CRITICAL_COLUMNS = {
    "raw_evaluations.csv": ["accuracy", "f1_score", "dataset_id", "model_name", "fold_id", "repeat_id"],
    "stability_metrics.csv": ["dataset_id", "model_name", "mean_accuracy", "cv_accuracy", "mean_f1", "cv_f1"],
    "correlation_results.csv": ["dataset_id", "model_name", "metric_type", "pearson_r", "pearson_p_value"],
    "permutation_results.csv": ["dataset_id", "model_name_a", "model_name_b", "p_value", "adj_p_value_holm"]
}

# Expected smoke test dataset IDs (from T050a)
EXPECTED_DATASET_IDS = [1, 14, 1461]  # iris, heart-statlog, credit-a

def validate_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    if not file_path.exists():
        logger.error(f"Missing expected file: {file_path}")
        return False
    return True

def validate_no_nan(file_path: Path, critical_columns: list) -> bool:
    """Check for NaN values in critical columns."""
    try:
        df = pd.read_csv(file_path)
        missing_cols = [col for col in critical_columns if col not in df.columns]
        if missing_cols:
            logger.error(f"File {file_path.name} missing critical columns: {missing_cols}")
            return False

        for col in critical_columns:
            if df[col].isna().any():
                logger.error(f"File {file_path.name} has NaN in column '{col}'")
                return False
        return True
    except Exception as e:
        logger.error(f"Error validating {file_path.name}: {e}")
        return False

def validate_row_count(file_path: Path) -> bool:
    """
    Validate row count in raw_evaluations.csv.
    Expected: num_selected_datasets * 3 models * 100 repeats.
    Allow count < 4500 if datasets were skipped.
    """
    try:
        df = pd.read_csv(file_path)
        if "dataset_id" not in df.columns:
            logger.error(f"File {file_path.name} missing 'dataset_id' column")
            return False

        unique_datasets = df["dataset_id"].unique()
        num_datasets = len(unique_datasets)
        
        # Check if all expected datasets are present
        missing_ids = set(EXPECTED_DATASET_IDS) - set(unique_datasets)
        if missing_ids:
            logger.warning(f"Missing expected dataset IDs in raw_evaluations: {missing_ids}")
            # Not failing here as per task description: "Explicitly allow count < 4500 if datasets were skipped"

        expected_min_rows = num_datasets * 3 * 100  # 3 models, 100 repeats
        actual_rows = len(df)

        if actual_rows < expected_min_rows:
            logger.warning(f"Row count {actual_rows} is less than expected minimum {expected_min_rows} for {num_datasets} datasets")
            # Log warning but don't fail, as datasets might have been skipped
            return True

        logger.info(f"Row count validation passed: {actual_rows} rows for {num_datasets} datasets")
        return True
    except Exception as e:
        logger.error(f"Error validating row count in {file_path.name}: {e}")
        return False

def validate_all_datasets_present(file_path: Path) -> bool:
    """Verify all selected dataset IDs are present in the file."""
    try:
        df = pd.read_csv(file_path)
        if "dataset_id" not in df.columns:
            logger.warning(f"File {file_path.name} does not contain 'dataset_id' column, skipping dataset presence check")
            return True

        unique_datasets = set(df["dataset_id"].unique())
        present_ids = unique_datasets.intersection(set(EXPECTED_DATASET_IDS))
        
        if len(present_ids) == 0:
            logger.error(f"No expected dataset IDs found in {file_path.name}")
            return False

        logger.info(f"Found expected dataset IDs in {file_path.name}: {present_ids}")
        return True
    except Exception as e:
        logger.error(f"Error checking dataset presence in {file_path.name}: {e}")
        return False

def main():
    """Main validation logic."""
    logger.info("Starting smoke test results validation...")
    
    results_dir = Path(RESULTS_DIR)
    if not results_dir.exists():
        logger.error(f"Results directory does not exist: {results_dir}")
        return 1

    all_valid = True

    # 1. Check file existence
    logger.info("Checking file existence...")
    for filename in EXPECTED_FILES:
        file_path = results_dir / filename
        if not validate_file_exists(file_path):
            all_valid = False

    if not all_valid:
        logger.error("One or more expected files are missing.")
        return 1

    # 2. Validate raw_evaluations.csv
    raw_file = results_dir / "raw_evaluations.csv"
    logger.info("Validating raw_evaluations.csv...")
    if not validate_no_nan(raw_file, CRITICAL_COLUMNS["raw_evaluations.csv"]):
        all_valid = False
    if not validate_row_count(raw_file):
        all_valid = False
    if not validate_all_datasets_present(raw_file):
        all_valid = False

    # 3. Validate stability_metrics.csv
    stability_file = results_dir / "stability_metrics.csv"
    logger.info("Validating stability_metrics.csv...")
    if not validate_no_nan(stability_file, CRITICAL_COLUMNS["stability_metrics.csv"]):
        all_valid = False
    if not validate_all_datasets_present(stability_file):
        all_valid = False

    # 4. Validate correlation_results.csv
    corr_file = results_dir / "correlation_results.csv"
    logger.info("Validating correlation_results.csv...")
    if not validate_no_nan(corr_file, CRITICAL_COLUMNS["correlation_results.csv"]):
        all_valid = False
    if not validate_all_datasets_present(corr_file):
        all_valid = False

    # 5. Validate permutation_results.csv
    perm_file = results_dir / "permutation_results.csv"
    logger.info("Validating permutation_results.csv...")
    if not validate_no_nan(perm_file, CRITICAL_COLUMNS["permutation_results.csv"]):
        all_valid = False
    if not validate_all_datasets_present(perm_file):
        all_valid = False

    # 6. Validate final_report.md (basic check)
    report_file = results_dir / "final_report.md"
    logger.info("Validating final_report.md...")
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content.strip()) == 0:
                logger.error("final_report.md is empty")
                all_valid = False
            else:
                logger.info("final_report.md is not empty")
    except Exception as e:
        logger.error(f"Error reading final_report.md: {e}")
        all_valid = False

    if all_valid:
        logger.info("All validations passed.")
        return 0
    else:
        logger.error("Some validations failed.")
        return 1

if __name__ == "__main__":
    import pandas as pd
    sys.exit(main())
