"""
Verification script for task T041b.
Checks that the results directory contains all expected artifacts:
- us1_correlation.json
- plot_scatter.png
- plot_timeseries.png
- quality_log.json
"""
import os
import sys
import json
from pathlib import Path

# Define the project root relative to this script
# Assuming this script is at code/verify_artifacts.py
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

EXPECTED_RESULTS = [
    "us1_correlation.json",
    "plot_scatter.png",
    "plot_timeseries.png"
]

EXPECTED_PROCESSED = [
    "quality_log.json"
]

def check_file_exists(path: Path, description: str) -> bool:
    if path.exists():
        print(f"[OK] {description} exists: {path}")
        return True
    else:
        print(f"[FAIL] {description} missing: {path}")
        return False

def main():
    all_ok = True

    # Check results directory
    if not RESULTS_DIR.exists():
        print(f"[FAIL] Results directory does not exist: {RESULTS_DIR}")
        return 1

    for filename in EXPECTED_RESULTS:
        filepath = RESULTS_DIR / filename
        if not check_file_exists(filepath, f"Results artifact '{filename}'"):
            all_ok = False

    # Check processed directory for quality_log.json
    if not PROCESSED_DIR.exists():
        print(f"[FAIL] Processed directory does not exist: {PROCESSED_DIR}")
        return 1

    for filename in EXPECTED_PROCESSED:
        filepath = PROCESSED_DIR / filename
        if not check_file_exists(filepath, f"Processed artifact '{filename}'"):
            all_ok = False

    # Validate JSON content if files exist
    json_path = RESULTS_DIR / "us1_correlation.json"
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            required_keys = ['pearson', 'spearman', 'p_val_permutation', 'optimal_lag']
            missing_keys = [k for k in required_keys if k not in data]
            if missing_keys:
                print(f"[FAIL] JSON missing keys: {missing_keys}")
                all_ok = False
            else:
                print(f"[OK] JSON schema valid with keys: {list(data.keys())}")
        except json.JSONDecodeError as e:
            print(f"[FAIL] Invalid JSON in {json_path}: {e}")
            all_ok = False

    quality_log_path = PROCESSED_DIR / "quality_log.json"
    if quality_log_path.exists():
        try:
            with open(quality_log_path, 'r') as f:
                data = json.load(f)
            print(f"[OK] Quality log valid: {type(data)}")
        except json.JSONDecodeError as e:
            print(f"[FAIL] Invalid JSON in {quality_log_path}: {e}")
            all_ok = False

    if all_ok:
        print("\n[SUCCESS] All expected artifacts are present and valid.")
        return 0
    else:
        print("\n[FAILURE] Some artifacts are missing or invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
