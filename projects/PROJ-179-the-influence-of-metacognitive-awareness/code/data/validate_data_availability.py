"""
T004: Validate Data Availability
Checks for the existence of a valid behavioral dataset containing 'confidence_rating' and 'source_label'.
Blocks execution if only OpenNeuro ds003386 (structural MRI) is found, as it lacks required behavioral fields.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging to file and stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/data_availability_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Known dataset identifiers and paths
OPENNEURO_DS003386_ID = "ds003386"
OPENNEURO_DS003386_BEHAVIORAL_FILE = DATA_DIR / "ds003386_behavioral.csv"
OPENNEURO_DS003386_RAW_DIR = DATA_DIR / "ds003386"

# Required fields for a valid behavioral dataset
REQUIRED_FIELDS = ['confidence_rating', 'source_label']

def check_openneuro_ds003386() -> tuple[bool, str]:
    """
    Checks if OpenNeuro ds003386 is present and if it contains required behavioral fields.
    Returns (is_valid, message).
    """
    logger.info(f"Checking OpenNeuro ds003386 availability...")
    
    # Check for the specific behavioral file that might have been manually downloaded
    if OPENNEURO_DS003386_BEHAVIORAL_FILE.exists():
        try:
            import pandas as pd
            df = pd.read_csv(OPENNEUTO_DS003386_BEHAVIORAL_FILE)
            missing_fields = [f for f in REQUIRED_FIELDS if f not in df.columns]
            if missing_fields:
                return False, f"File exists but missing fields: {missing_fields}"
            return True, "Valid behavioral file found."
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    # Check for raw directory structure (typical BIDS)
    if OPENNEURO_DS003386_RAW_DIR.exists():
        # Check for participants.tsv or similar metadata
        # ds003386 is primarily structural MRI, usually lacks deep behavioral trials
        # We simulate the check: if only raw MRI data is present, it's invalid for this study
        logger.warning(f"OpenNeuro ds003386 directory found at {OPENNEURO_DS003386_RAW_DIR}, but no valid behavioral CSV detected.")
        return False, "OpenNeuro ds003386 lacks required behavioral fields (confidence_rating, source_label)."
    
    return False, "OpenNeuro ds003386 not found locally."

def check_alternative_datasets() -> tuple[bool, str, str]:
    """
    Scans the data directory for other potential behavioral datasets.
    Returns (is_valid, message, path).
    """
    logger.info("Scanning for alternative behavioral datasets...")
    
    if not DATA_DIR.exists():
        return False, "Data directory does not exist.", ""
    
    valid_dataset_path = None
    valid_dataset_name = None
    
    # Heuristic: Look for CSV files that might contain the required columns
    # We check a few common naming patterns
    potential_files = list(DATA_DIR.glob("*.csv"))
    
    for file_path in potential_files:
        if "ds003386" in file_path.name:
            continue # Skip the known invalid one again
        
        try:
            import pandas as pd
            # Read just the header to check columns
            df = pd.read_csv(file_path, nrows=0)
            if all(field in df.columns for field in REQUIRED_FIELDS):
                return True, f"Valid dataset found: {file_path.name}", str(file_path)
        except Exception:
            continue
    
    return False, "No valid alternative behavioral datasets found.", ""

def main():
    logger.info("Starting data availability validation (T004)...")
    
    # 1. Check OpenNeuro ds003386
    is_ds003386_valid, ds003386_msg = check_openneuro_ds003386()
    
    if is_ds003386_valid:
        logger.info(f"SUCCESS: Valid dataset found: OpenNeuro ds003386 behavioral file.")
        print(json.dumps({"status": "PASS", "source": "OpenNeuro ds003386", "message": ds003386_msg}))
        sys.exit(0)
    
    # 2. If ds003386 is invalid or missing, check alternatives
    logger.warning(f"OpenNeuro ds003386 check result: {ds003386_msg}")
    
    is_alt_valid, alt_msg, alt_path = check_alternative_datasets()
    
    if is_alt_valid:
        logger.info(f"SUCCESS: Valid dataset found: {alt_path}")
        print(json.dumps({"status": "PASS", "source": alt_path, "message": alt_msg}))
        sys.exit(0)
    
    # 3. If no valid dataset found, block the project
    logger.error("ERROR: Project blocked. No valid behavioral dataset found.")
    logger.error("OpenNeuro ds003386 lacks required behavioral fields. Aborting.")
    logger.error("Please download a valid behavioral dataset containing 'confidence_rating' and 'source_label' to the data/ directory.")
    
    print(json.dumps({"status": "FAIL", "message": "ERROR: Project blocked. OpenNeuro ds003386 lacks required behavioral fields. Aborting."}))
    sys.exit(1)

if __name__ == "__main__":
    main()