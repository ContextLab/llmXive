"""
validate_columns.py

Verifies the presence of required motion parameters and FD estimates in the
HCP (ds001734) dataset structure before ingestion proceeds.

This script scans the expected directory structure for fMRI preprocessed files
(typically .tsv or .csv) and ensures that columns for rigid-body motion parameters
(e.g., trans_x, trans_y, trans_z, rot_x, rot_y, rot_z) and Framewise Displacement (FD)
are present.

It exits with code 0 if validation passes, or non-zero with an error message if
required columns are missing.
"""

import sys
import os
import argparse
import pandas as pd
from pathlib import Path
from typing import List, Set, Dict, Optional

# Required motion parameters typically found in HCP fMRIPrep outputs
REQUIRED_MOTION_COLS: Set[str] = {
    "trans_x", "trans_y", "trans_z",
    "rot_x", "rot_y", "rot_z"
}

# Required FD column
REQUIRED_FD_COLS: Set[str] = {
    "fd"
}

# Allow common variations if necessary, but strictly require at least one set
# For HCP ds001734, standard fMRIPrep outputs usually use the names above.
# We will check for the standard set.

def find_motion_files(data_root: Path) -> List[Path]:
    """
    Recursively find potential motion parameter files (typically .tsv)
    in the data directory structure.
    """
    candidates = []
    # Common patterns for motion files in fMRIPrep derivatives
    patterns = ["*_confounds_regressors.tsv", "*confounds.tsv"]
    
    for pattern in patterns:
        candidates.extend(data_root.rglob(pattern))
    
    # Fallback: any tsv file in a 'confounds' or 'motion' folder if specific names fail
    if not candidates:
        for root, dirs, files in os.walk(data_root):
            for f in files:
                if f.endswith(".tsv") and ("confound" in f.lower() or "motion" in f.lower()):
                    candidates.append(Path(root) / f)
    
    return list(set(candidates))

def validate_file_columns(file_path: Path) -> Dict[str, bool]:
    """
    Checks if a specific file contains the required motion and FD columns.
    Returns a dict with validation status.
    """
    try:
        # Read just the header to save memory
        df = pd.read_csv(file_path, sep="\t", nrows=0)
        columns = set(df.columns)
        
        has_motion = REQUIRED_MOTION_COLS.issubset(columns)
        has_fd = REQUIRED_FD_COLS.issubset(columns)
        
        missing_motion = REQUIRED_MOTION_COLS - columns
        missing_fd = REQUIRED_FD_COLS - columns
        
        return {
            "valid": has_motion and has_fd,
            "has_motion": has_motion,
            "has_fd": has_fd,
            "missing_motion": list(missing_motion),
            "missing_fd": list(missing_fd),
            "file": str(file_path)
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "file": str(file_path)
        }

def main():
    parser = argparse.ArgumentParser(
        description="Validate motion parameters and FD estimates in dataset."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data/raw_fmri"),
        help="Root directory of the dataset to validate (default: data/raw_fmri)"
    )
    
    args = parser.parse_args()
    data_root = args.data_root
    
    if not data_root.exists():
        print(f"Error: Data root directory '{data_root}' does not exist.")
        print("Ensure the dataset has been downloaded (T011) and directories initialized (T006).")
        sys.exit(1)

    motion_files = find_motion_files(data_root)
    
    if not motion_files:
        print(f"Error: No motion parameter files (confounds) found in '{data_root}'.")
        print("Ensure the dataset has been downloaded and preprocessed (T011/T012).")
        sys.exit(1)

    print(f"Found {len(motion_files)} candidate motion parameter files.")
    
    all_valid = True
    errors = []

    for file_path in motion_files:
        result = validate_file_columns(file_path)
        if result["valid"]:
            print(f"OK: {file_path}")
        else:
            all_valid = False
            errors.append(result)
            print(f"FAIL: {file_path}")
            if "error" in result:
                print(f"  Error: {result['error']}")
            else:
                if not result["has_motion"]:
                    print(f"  Missing motion params: {result['missing_motion']}")
                if not result["has_fd"]:
                    print(f"  Missing FD column: {result['missing_fd']}")

    if all_valid:
        print("\nValidation PASSED: All required motion parameters and FD estimates present.")
        sys.exit(0)
    else:
        print(f"\nValidation FAILED: {len(errors)} file(s) missing required columns.")
        sys.exit(1)

if __name__ == "__main__":
    main()