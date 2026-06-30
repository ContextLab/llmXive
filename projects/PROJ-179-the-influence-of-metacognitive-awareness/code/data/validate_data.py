import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Import config with tolerant access
try:
    from config.env_config import load_config, CONFIG
except ImportError:
    # Fallback for if config is not yet fully ready or path issues
    class FallbackConfig:
        def get(self, section, default=None):
            return default if default else {}
    CONFIG = FallbackConfig()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ['confidence_rating', 'source_label']

def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load the dataset from the specified path.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Dataset not found at {file_path}. Ensure T005 (download.py) has successfully executed.")
        raise FileNotFoundError(f"Dataset not found at {file_path}")
    
    logger.info(f"Loading dataset from {file_path}...")
    
    # Try to infer format based on extension
    if path.suffix.lower() == '.csv':
        df = pd.read_csv(path)
    elif path.suffix.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(path)
    elif path.suffix.lower() == '.json':
        df = pd.read_json(path)
    else:
        # Default to CSV if unknown
        df = pd.read_csv(path)
        
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
    return df

def validate_fields(df: pd.DataFrame) -> bool:
    """
    Validate that the dataset contains the required behavioral fields.
    Raises ValueError if fields are missing.
    """
    missing_fields = []
    for field in REQUIRED_FIELDS:
        if field not in df.columns:
            missing_fields.append(field)
    
    if missing_fields:
        error_msg = f"Required fields missing: {', '.join(missing_fields)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("All required fields present.")
    return True

def write_report(status: str, message: str, output_path: str):
    """
    Write the validation report to a JSON file.
    """
    report = {
        "status": status,
        "message": message,
        "fields_checked": REQUIRED_FIELDS,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {output_path}")

def main():
    """
    Main entry point for data validation (T006).
    """
    logger.info("Starting data validation (T006)...")
    
    # Determine input file path
    # T005 downloads to data/ds003386_behavioral.csv based on task description
    # We check common locations
    possible_paths = [
        "data/ds003386_behavioral.csv",
        "data/downloaded/ds003386_behavioral.csv",
        "data/behavioral_data.csv"
    ]
    
    input_file = None
    for p in possible_paths:
        if os.path.exists(p):
            input_file = p
            break
    
    if not input_file:
        # If T005 hasn't run or file is in a different location, we might need to check CONFIG
        # But strictly following T006 spec: "check for required behavioral fields in the downloaded dataset"
        # If the expected file from T005 is missing, we fail gracefully.
        logger.error(f"Could not find downloaded dataset. Expected one of: {possible_paths}")
        write_report("FAIL", "Dataset file not found. Ensure T005 has completed successfully.", "data/validation_report.json")
        sys.exit(1)
    
    try:
        df = load_dataset(input_file)
        validate_fields(df)
        write_report("PASS", "All required fields present and valid.", "data/validation_report.json")
        logger.info("Validation completed successfully.")
        sys.exit(0)
    except ValueError as e:
        write_report("FAIL", str(e), "data/validation_report.json")
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        write_report("FAIL", f"Unexpected error: {str(e)}", "data/validation_report.json")
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()