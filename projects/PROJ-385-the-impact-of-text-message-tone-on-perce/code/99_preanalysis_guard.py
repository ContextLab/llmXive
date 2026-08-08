"""
Pre-analysis Guard Task T092.

Verifies that the LMM script (code/04_fit_lmm.py) reads directly from
data/processed/anonymised_ratings.csv. The script must exit with an error
if it attempts to load any raw file (e.g., from data/raw/).

This guard ensures data privacy and pipeline integrity by enforcing the
use of anonymised data for statistical analysis.
"""
import sys
import re
from pathlib import Path

# Add project root to path to import config if needed, 
# though we can use standard pathlib for this check.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LMM_SCRIPT_PATH = PROJECT_ROOT / "code" / "04_fit_lmm.py"
ALLOWED_INPUT = PROJECT_ROOT / "data" / "processed" / "anonymised_ratings.csv"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Patterns indicating raw data access
RAW_FILE_PATTERNS = [
  r"data/raw/real_ratings\.csv",
  r"data/raw/stimuli\.csv",
  r"raw/real_ratings",
  r"raw/stimuli",
  r"PROLIFIC_ID", # Direct usage of raw ID column often implies raw file
  r"prolific_id"  # Case insensitive check below
]

def check_lmm_script():
    """
    Scans the LMM script for forbidden raw data imports.
    Returns True if the script is compliant, False otherwise.
    """
    if not LMM_SCRIPT_PATH.exists():
        print(f"ERROR: LMM script not found at {LMM_SCRIPT_PATH}")
        return False

    try:
        content = LMM_SCRIPT_PATH.read_text(encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Could not read LMM script: {e}")
        return False

    # Check 1: Ensure the script attempts to load the allowed file
    # We look for the specific path or the function call that resolves to it.
    # Since the task requires reading from 'data/processed/anonymised_ratings.csv',
    # we verify the string exists in the code.
    allowed_path_str = str(ALLOWED_INPUT)
    if allowed_path_str not in content:
        # It might use a helper function, but if the path isn't there at all,
        # it's suspicious. However, let's be slightly lenient and check for
        # the filename pattern if the full path is constructed dynamically.
        if "anonymised_ratings.csv" not in content:
            print(f"ERROR: Script does not explicitly reference the allowed input file: {allowed_path_str}")
            print("The script must read from 'data/processed/anonymised_ratings.csv'.")
            return False

    # Check 2: Ensure the script does NOT load raw files
    for pattern in RAW_FILE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            print(f"ERROR: Script attempts to load raw data or use raw identifiers matching '{pattern}'")
            print("The LMM script must NOT load files from data/raw/ or use raw Prolific IDs.")
            return False

    # Check 3: Verify imports of helper functions that might bypass checks
    # (Optional: check if it imports a 'load_raw' function)
    if "load_raw" in content or "load_real_ratings" in content:
        # If it imports a function named 'load_real_ratings', it might be loading raw data.
        # We need to be careful not to flag 'load_ratings' if that's the generic name.
        # But 'load_real_ratings' is a strong indicator of raw data usage.
        if "load_real_ratings" in content:
            print("WARNING: Script imports 'load_real_ratings'. This suggests direct raw data access.")
            # We will fail the guard if it tries to use this function for the LMM input.
            # For a strict guard, we fail if the function name exists and is used.
            if "load_real_ratings(" in content:
                print("ERROR: Direct usage of load_real_ratings detected.")
                return False

    print("SUCCESS: LMM script passed the pre-analysis guard.")
    print(f"Verified input: {allowed_path_str}")
    return True

def main():
    print("Running Pre-Analysis Guard (T092)...")
    if not check_lmm_script():
        print("GUARD FAILED: The LMM script is not compliant.")
        sys.exit(1)
    print("Guard check completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()