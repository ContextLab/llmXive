"""
T019c: Verify existence and count of shuffled files.

This script verifies that the null distribution generation tasks (T019a and T019b)
have successfully created the required number of shuffled files (1000 per series)
in both the real and synthetic directories.

Output: data/results/null_distribution_gate.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_path
from src.utils.logging import setup_logger, log_info, log_error, log_warning

# Constants
EXPECTED_COUNT = 1000  # From tasks.md: "counts match 1000 per series"
REAL_DIR_NAME = "real"
SYNTHETIC_DIR_NAME = "synthetic"
NULL_DISTRIBUTIONS_BASE = "data/processed/null_distributions"
RESULTS_DIR = "data/results"
OUTPUT_FILE = "null_distribution_gate.json"

def get_series_ids(directory: Path) -> List[str]:
    """
    Extract unique series IDs from the directory structure.
    
    The directory structure is expected to be:
    directory/source_id/shuffle_*.csv OR directory/source_id_shuffles.csv
    
    Returns a list of unique source IDs.
    """
    series_ids = set()
    
    if not directory.exists():
        return []
    
    # Check for consolidated files first (pattern: source_id_shuffles.csv)
    for file in directory.glob("*_shuffles.csv"):
        # Extract ID from filename: source_id_shuffles.csv -> source_id
        series_ids.add(file.stem.replace("_shuffles", ""))
    
    # Check for individual files or subdirectories
    for item in directory.iterdir():
        if item.is_dir():
            series_ids.add(item.name)
        elif item.is_file() and item.suffix == ".csv":
            # If it's a shuffle file, extract ID
            if "_shuffle_" in item.name:
                # Pattern: source_id_shuffle_001.csv -> source_id
                base_name = item.name.rsplit("_shuffle_", 1)[0]
                series_ids.add(base_name)
            elif item.name.endswith("_shuffles.csv"):
                # Already handled above, but just in case
                series_ids.add(item.stem.replace("_shuffles", ""))
    
    return sorted(list(series_ids))

def count_shuffled_files(directory: Path, series_id: str) -> int:
    """
    Count the number of shuffled files for a given series ID.
    
    Handles both individual files and consolidated CSV files.
    """
    count = 0
    
    # Check for consolidated file: source_id_shuffles.csv
    consolidated_file = directory / f"{series_id}_shuffles.csv"
    if consolidated_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(consolidated_file)
            # Check if there's a shuffle_id column
            if "shuffle_id" in df.columns:
                count = df["shuffle_id"].nunique()
            else:
                # If no shuffle_id column, assume each row is a shuffle
                count = len(df)
        except Exception as e:
            log_warning(f"Failed to read consolidated file {consolidated_file}: {e}")
            return 0
    
    # Check for individual files: source_id_shuffle_*.csv
    if count == 0:
        individual_pattern = directory / f"{series_id}_shuffle_*.csv"
        count = len(list(directory.glob(individual_pattern)))
    
    # Check for subdirectory with individual files
    if count == 0:
        series_dir = directory / series_id
        if series_dir.exists() and series_dir.is_dir():
            individual_files = list(series_dir.glob("shuffle_*.csv"))
            count = len(individual_files)
    
    return count

def verify_null_distributions(base_dir: Path, dir_type: str) -> Dict[str, Any]:
    """
    Verify null distributions for a specific directory type (real or synthetic).
    
    Returns a dictionary with verification results.
    """
    target_dir = base_dir / dir_type
    
    result = {
        "directory_type": dir_type,
        "target_directory": str(target_dir),
        "exists": target_dir.exists(),
        "series": {},
        "total_series": 0,
        "total_files": 0,
        "all_pass": True,
        "errors": []
    }
    
    if not result["exists"]:
        result["errors"].append(f"Directory does not exist: {target_dir}")
        result["all_pass"] = False
        return result
    
    series_ids = get_series_ids(target_dir)
    result["total_series"] = len(series_ids)
    
    if len(series_ids) == 0:
        result["errors"].append("No series IDs found in directory")
        result["all_pass"] = False
        return result
    
    log_info(f"Found {len(series_ids)} series in {dir_type} directory")
    
    for series_id in series_ids:
        count = count_shuffled_files(target_dir, series_id)
        passed = count == EXPECTED_COUNT
        
        result["series"][series_id] = {
            "count": count,
            "expected": EXPECTED_COUNT,
            "passed": passed,
            "status": "PASS" if passed else "FAIL"
        }
        
        result["total_files"] += count
        
        if not passed:
            result["all_pass"] = False
            error_msg = f"Series '{series_id}' has {count} files, expected {EXPECTED_COUNT}"
            result["errors"].append(error_msg)
            log_warning(error_msg)
        else:
            log_info(f"Series '{series_id}': {count} shuffled files (PASS)")
    
    return result

def main():
    """
    Main function to verify null distribution files and write gate results.
    """
    setup_logger(level=logging.INFO)
    
    # Get paths
    project_root = Path(__file__).resolve().parent.parent
    base_dir = project_root / NULL_DISTRIBUTIONS_BASE
    results_dir = project_root / RESULTS_DIR
    output_path = results_dir / OUTPUT_FILE
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    log_info("Starting null distribution gate verification (T019c)")
    
    # Verify real null distributions
    real_result = verify_null_distributions(base_dir, REAL_DIR_NAME)
    
    # Verify synthetic null distributions
    synthetic_result = verify_null_distributions(base_dir, SYNTHETIC_DIR_NAME)
    
    # Determine overall gate status
    gate_passed = real_result["all_pass"] and synthetic_result["all_pass"]
    
    # Compile final result
    gate_result = {
        "task_id": "T019c",
        "status": "PASS" if gate_passed else "FAIL",
        "timestamp": str(Path(__file__).stat().st_mtime),  # Using file mod time as proxy
        "expected_count_per_series": EXPECTED_COUNT,
        "real": real_result,
        "synthetic": synthetic_result,
        "all_errors": real_result["errors"] + synthetic_result["errors"]
    }
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(gate_result, f, indent=2)
    
    log_info(f"Gate verification complete. Status: {gate_result['status']}")
    log_info(f"Results written to: {output_path}")
    
    if gate_passed:
        log_info("All null distribution counts match expected values.")
        return 0
    else:
        log_error("Gate verification failed. See errors above.")
        for error in gate_result["all_errors"]:
            log_error(f"  - {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())