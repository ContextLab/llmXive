"""
T035a: Validate schema of data/processed/features.csv.

This script validates the feature schema contract:
1. Checks for required columns.
2. Checks for null values.
3. Validates RT range (100-2000 ms).
4. Writes a validation log to data/processed/feature_validation_log.json.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config import get_path, ensure_dirs

REQUIRED_COLUMNS = [
    "participant_id",
    "median_rt",
    "delta_rel",
    "theta_rel",
    "alpha_rel",
    "low_beta_rel",
    "high_beta_rel",
    "gamma_rel"
]

RT_MIN = 100.0
RT_MAX = 2000.0

def validate_schema():
    """
    Validates the schema of data/processed/features.csv against the contract.
    Returns a dictionary with validation results.
    """
    features_path = get_path("data_processed", "features.csv")
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "file_path": features_path,
        "status": "failed",
        "errors": [],
        "warnings": []
    }

    if not os.path.exists(features_path):
        validation_results["errors"].append(f"File not found: {features_path}")
        return validation_results

    try:
        df = pd.read_csv(features_path)
    except Exception as e:
        validation_results["errors"].append(f"Failed to read CSV: {str(e)}")
        return validation_results

    # 1. Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        validation_results["errors"].append(f"Missing columns: {missing_cols}")
    else:
        validation_results["checks"]["columns"] = "passed"

    # 2. Check for nulls
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()
    if total_nulls > 0:
        validation_results["errors"].append(f"Found {total_nulls} null values.")
        validation_results["null_counts"] = null_counts.to_dict()
    else:
        validation_results["checks"]["no_nulls"] = "passed"

    # 3. Check RT range
    if "median_rt" in df.columns:
        rt_below = (df["median_rt"] < RT_MIN).sum()
        rt_above = (df["median_rt"] > RT_MAX).sum()
        if rt_below > 0:
            validation_results["errors"].append(f"Found {rt_below} RT values below {RT_MIN}ms.")
        if rt_above > 0:
            validation_results["errors"].append(f"Found {rt_above} RT values above {RT_MAX}ms.")
        if rt_below == 0 and rt_above == 0:
            validation_results["checks"]["rt_range"] = "passed"

    # 4. Check unique participant_id
    if "participant_id" in df.columns:
        if df["participant_id"].duplicated().any():
            validation_results["warnings"].append("Duplicate participant_ids found.")
        else:
            validation_results["checks"]["unique_participant_id"] = "passed"

    if not validation_results["errors"]:
        validation_results["status"] = "passed"
    
    return validation_results

def main():
    parser = argparse.ArgumentParser(description="Validate feature schema.")
    parser.add_argument("--output", type=str, default=None, 
                        help="Path to write validation log (default: data/processed/feature_validation_log.json)")
    args = parser.parse_args()

    print("Starting feature schema validation...")
    results = validate_schema()

    # Print results
    print(f"Validation Status: {results['status']}")
    if results["errors"]:
        print("Errors:")
        for err in results["errors"]:
            print(f"  - {err}")
    if results["warnings"]:
        print("Warnings:")
        for warn in results["warnings"]:
            print(f"  - {warn}")

    # Write log
    log_path = args.output
    if not log_path:
        log_path = get_path("data_processed", "feature_validation_log.json")
    
    # Ensure directory exists
    ensure_dirs(Path(log_path).parent)

    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Validation log written to: {log_path}")

    # Exit with error code if validation failed
    if results["status"] == "failed":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()