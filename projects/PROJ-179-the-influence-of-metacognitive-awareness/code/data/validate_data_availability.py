"""
T004: Data Availability Validation Gate

Checks for the existence of a VALID behavioral dataset containing 
'confidence_rating' and 'source_label'.

Logic:
1. Check for OpenNeuro ds003386. If detected as the ONLY source, 
   exit with code 1 and log the specific error message.
2. If a valid behavioral dataset is found (with required columns), 
   log success and exit with code 0.
3. Fallback: Search for alternative datasets. If none found, exit 1.
"""
import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd

# Setup logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/data_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_COLUMNS = ['confidence_rating', 'source_label']
OPENNEURO_DS003386_NAME = 'ds003386'

# Expected paths for potential data sources
DATA_DIR = Path('data')
POTENTIAL_FILES = [
    DATA_DIR / 'behavioral_data.csv',
    DATA_DIR / 'downloaded' / 'behavioral_data.csv',
    DATA_DIR / 'ds003386_behavioral.csv',
    DATA_DIR / 'downloaded' / 'ds003386_behavioral.csv',
    DATA_DIR / 'derived' / 'trial_data.csv',  # If already processed
]

def check_openneuro_ds003386():
    """
    Check if OpenNeuro ds003386 is present.
    Returns:
        tuple: (is_present: bool, is_valid: bool)
        - is_present: True if the dataset file/directory exists.
        - is_valid: True if it contains required behavioral columns.
    """
    # Check for local file indicators
    possible_paths = [
        DATA_DIR / 'ds003386',
        DATA_DIR / 'ds003386_behavioral.csv',
        DATA_DIR / 'downloaded' / 'ds003386_behavioral.csv',
        DATA_DIR / 'downloaded' / 'ds003386',
    ]
    
    found_path = None
    for p in possible_paths:
        if p.exists():
            found_path = p
            break
    
    if not found_path:
        logger.info(f"OpenNeuro {OPENNEURO_DS003386_NAME} not found locally.")
        return False, False
    
    logger.info(f"Found potential OpenNeuro {OPENNEURO_DS003386_NAME} at {found_path}")
    
    # Try to load and validate
    try:
        if found_path.suffix == '.csv':
            df = pd.read_csv(found_path)
        elif found_path.is_dir():
            # Try to find a TSV/CSV in the directory
            ts_files = list(found_path.glob('**/*.tsv')) + list(found_path.glob('**/*.csv'))
            if not ts_files:
                logger.warning(f"Found directory {found_path} but no CSV/TSV files.")
                return True, False
            # Assume the first behavioral file found is the one
            target_file = ts_files[0]
            df = pd.read_csv(target_file)
        else:
            logger.warning(f"Found path {found_path} but cannot determine format.")
            return True, False
        
        # Check for required columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.warning(f"OpenNeuro {OPENNEURO_DS003386_NAME} lacks required columns: {missing_cols}")
            return True, False
        
        logger.info(f"OpenNeuro {OPENNEURO_DS003386_NAME} has required columns.")
        return True, True
        
    except Exception as e:
        logger.error(f"Error reading OpenNeuro {OPENNEURO_DS003386_NAME}: {e}")
        return True, False

def check_alternative_datasets():
    """
    Search for alternative valid behavioral datasets.
    Returns:
        tuple: (found: bool, path: Path or None, df: DataFrame or None)
    """
    logger.info("Scanning for alternative behavioral datasets...")
    
    for file_path in POTENTIAL_FILES:
        if file_path.exists():
            try:
                logger.info(f"Checking candidate: {file_path}")
                if file_path.suffix == '.csv':
                    df = pd.read_csv(file_path)
                elif file_path.suffix == '.tsv':
                    df = pd.read_csv(file_path, sep='\t')
                else:
                    continue
                
                # Check for required columns
                present_cols = [col for col in REQUIRED_COLUMNS if col in df.columns]
                if len(present_cols) == len(REQUIRED_COLUMNS):
                    logger.info(f"Valid dataset found at: {file_path}")
                    return True, file_path, df
                else:
                    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
                    logger.info(f"File {file_path} missing columns: {missing}")
                    
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
    
    logger.error("No valid behavioral dataset found in expected locations.")
    return False, None, None

def main():
    logger.info("Starting data availability validation (T004)...")
    
    # 1. Check OpenNeuro ds003386
    is_present, is_valid = check_openneuro_ds003386()
    
    if is_present and not is_valid:
        # If ds003386 is the only source found and it's invalid, block the project
        # Check if any other valid dataset exists
        alt_found, alt_path, _ = check_alternative_datasets()
        
        if not alt_found:
            error_msg = f"ERROR: Project blocked. OpenNeuro {OPENNEURO_DS003386_NAME} lacks required behavioral fields. Aborting."
            logger.error(error_msg)
            
            # Write failure report
            report = {
                "status": "FAIL",
                "message": error_msg,
                "blocked_dataset": OPENNEURO_DS003386_NAME,
                "reason": "Missing required columns: " + ", ".join(REQUIRED_COLUMNS)
            }
            
            report_path = DATA_DIR / 'validation_report.json'
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            sys.exit(1)
    
    # 2. Check for valid behavioral dataset
    found, path, df = check_alternative_datasets()
    
    if found:
        logger.info("SUCCESS: Valid behavioral dataset found.")
        report = {
            "status": "PASS",
            "message": "Valid behavioral dataset found.",
            "dataset_path": str(path),
            "columns_found": REQUIRED_COLUMNS
        }
        
        report_path = DATA_DIR / 'validation_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        sys.exit(0)
    else:
        # If ds003386 was found but invalid, and no alternatives, we already exited above.
        # If ds003386 was not found and no alternatives, block.
        error_msg = "ERROR: Project blocked. No valid behavioral dataset found."
        logger.error(error_msg)
        
        report = {
            "status": "FAIL",
            "message": error_msg,
            "reason": "No dataset with required columns found."
        }
        
        report_path = DATA_DIR / 'validation_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        sys.exit(1)

if __name__ == "__main__":
    main()