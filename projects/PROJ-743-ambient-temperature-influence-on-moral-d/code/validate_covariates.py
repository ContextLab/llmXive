"""
T028e: Validate Covariate Integrity

Ensures all derived covariate files (demographics, dilemma_choice, dilemma_complexity, time_of_day)
are complete, have no missing rows, and match the participant set from the primary merged dataset.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Set, List, Any

import pandas as pd
import numpy as np

# Import from existing project modules to align with API surface
from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate covariate integrity against merged dataset.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/merged_dataset.parquet",
        help="Path to the merged dataset (primary source of truth)."
    )
    parser.add_argument(
        "--covariates-dir",
        type=str,
        default="data/processed",
        help="Directory containing derived covariate CSV files."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/logs/covariate_validation.json",
        help="Path to save the validation report JSON."
    )
    return parser.parse_args()

def load_covariate_file(path: Path) -> pd.DataFrame:
    """Load a CSV covariate file safely."""
    if not path.exists():
        raise FileNotFoundError(f"Covariate file not found: {path}")
    try:
        return pd.read_csv(path)
    except Exception as e:
        raise RuntimeError(f"Failed to load {path}: {e}")

def validate_covariate_file(
    name: str,
    df: pd.DataFrame,
    valid_participant_ids: Set[str],
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Validate a single covariate file:
    1. Check for missing rows (NaN in critical columns).
    2. Check that all participant_ids exist in the main merged dataset.
    3. Check for duplicates if applicable.
    """
    issues = []
    status = "pass"

    if df.empty:
        issues.append("File is empty.")
        return {"status": "fail", "issues": issues}

    # 1. Check for missing values in participant_id
    if "participant_id" not in df.columns:
        issues.append("Missing 'participant_id' column.")
        return {"status": "fail", "issues": issues}

    missing_pid = df["participant_id"].isna().sum()
    if missing_pid > 0:
        issues.append(f"Found {missing_pid} rows with missing participant_id.")
        status = "fail"

    # 2. Check for missing values in other critical columns
    # We assume all columns in the covariate file are critical for integrity
    non_pid_cols = [c for c in df.columns if c != "participant_id"]
    for col in non_pid_cols:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            issues.append(f"Column '{col}' has {missing_count} missing values.")
            status = "fail"

    # 3. Check participant ID membership
    current_ids = set(df["participant_id"].dropna().astype(str))
    invalid_ids = current_ids - valid_participant_ids
    if invalid_ids:
        issues.append(f"Found {len(invalid_ids)} participant_ids not in merged dataset.")
        # Log first 5 for debugging
        if len(invalid_ids) > 0:
            issues.append(f"Sample invalid IDs: {list(invalid_ids)[:5]}")
        status = "fail"

    # 4. Check for duplicates
    if df.duplicated(subset=["participant_id"]).any():
        dup_count = df.duplicated(subset=["participant_id"]).sum()
        issues.append(f"Found {dup_count} duplicate participant_ids.")
        status = "fail"

    logger.info(f"Validation for {name}: {status}")
    if issues:
        for issue in issues:
            logger.warning(f"  - {issue}")

    return {
        "status": status,
        "row_count": len(df),
        "issues": issues
    }

def main() -> int:
    args = parse_args()
    
    # Setup logging
    log_dir = Path(args.output).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = get_data_quality_logger("covariate_validation")
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting covariate validation. Input: {args.input}")

    # 1. Load the primary merged dataset
    try:
        merged_df = pd.read_parquet(args.input)
    except Exception as e:
        logger.error(f"Failed to load merged dataset: {e}")
        # Write failure report and exit
        report = {
            "status": "fail",
            "reason": f"Could not load merged dataset: {e}",
            "covariates": {}
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        return 1

    if merged_df.empty:
        logger.error("Merged dataset is empty.")
        report = {"status": "fail", "reason": "Merged dataset is empty", "covariates": {}}
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        return 1

    # Extract valid participant IDs
    valid_participant_ids = set(merged_df["participant_id"].dropna().astype(str))
    logger.info(f"Loaded {len(valid_participant_ids)} unique participant IDs from merged dataset.")

    # 2. Define expected covariate files based on T028a-d
    # T028a: demographics (covariates.csv)
    # T028b: dilemma_choice (dilemma_choices.csv)
    # T028c: dilemma_complexity (dilemma_complexity.csv)
    # T028d: time_of_day (time_of_day.csv)
    
    covariate_files = [
        ("demographics", "covariates.csv"),
        ("dilemma_choice", "dilemma_choices.csv"),
        ("dilemma_complexity", "dilemma_complexity.csv"),
        ("time_of_day", "time_of_day.csv")
    ]

    results = {}
    all_pass = True

    for name, filename in covariate_files:
        file_path = Path(args.covariates_dir) / filename
        if not file_path.exists():
            logger.warning(f"Covariate file missing: {filename}")
            results[name] = {
                "status": "fail",
                "reason": "File not found",
                "issues": ["File not found"]
            }
            all_pass = False
            continue

        try:
            df = load_covariate_file(file_path)
            result = validate_covariate_file(name, df, valid_participant_ids, logger)
            results[name] = result
            if result["status"] == "fail":
                all_pass = False
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            results[name] = {
                "status": "fail",
                "reason": str(e),
                "issues": [str(e)]
            }
            all_pass = False

    # 3. Final Report
    final_status = "pass" if all_pass else "fail"
    report = {
        "status": final_status,
        "total_participants_in_merged": len(valid_participant_ids),
        "covariates": results
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation complete. Status: {final_status}. Report saved to {output_path}")
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())