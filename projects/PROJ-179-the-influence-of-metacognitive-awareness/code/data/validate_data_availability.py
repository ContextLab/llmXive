"""
T004: Validate Data Availability
Checks for the existence of a VALID behavioral dataset containing 'confidence_rating' and 'source_label'.
Exits with code 1 if only invalid sources (e.g., OpenNeuro ds003386) are found.
"""
import os
import sys
import logging
from pathlib import Path
import requests
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "derived"
REQUIRED_COLUMNS = ['confidence_rating', 'source_label']

# Known dataset sources
DATASETS = {
    "openneuro_ds003386": {
        "name": "OpenNeuro ds003386 (structural MRI)",
        "type": "structural_mri",
        "url": "https://openneuro.org/datasets/ds003386",
        "behavioral": False,
        "reason": "Lacks required behavioral fields (confidence_rating, source_label)"
    },
    "openneuro_ds004042": {
        "name": "OpenNeuro ds004042 (Behavioral)",
        "type": "behavioral",
        "url": "https://openneuro.org/datasets/ds004042",
        "behavioral": True,
        "requires_check": True,
        "note": "Needs validation for specific columns"
    },
    "psychopy_sample": {
        "name": "PsychoPy Behavioral Metacognition Sample",
        "type": "behavioral",
        "url": "https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv",
        "behavioral": True,
        "requires_check": True
    },
    "uciml_metacognition": {
        "name": "UCI Metacognition Dataset (Simulated)",
        "type": "behavioral",
        "url": "https://raw.githubusercontent.com/llmXive/datasets/main/sample_behavioral_data.csv",
        "behavioral": True,
        "requires_check": True
    }
}

def check_openneuro_ds003386():
    """Check if OpenNeuro ds003386 is the only available source."""
    logger.info("Checking for OpenNeuro ds003386...")
    # ds003386 is structural MRI, not behavioral
    return DATASETS["openneuro_ds003386"]

def validate_columns(df, dataset_name):
    """Check if the dataframe has required columns."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        logger.warning(f"Dataset '{dataset_name}' missing required columns: {missing}")
        return False
    logger.info(f"Dataset '{dataset_name}' has required columns: {REQUIRED_COLUMNS}")
    return True

def check_alternative_datasets():
    """Search for alternative behavioral datasets."""
    logger.info("Searching for alternative behavioral datasets...")
    
    valid_dataset = None
    
    # Try to download and validate each alternative
    for key, info in DATASETS.items():
        if key == "openneuro_ds003386" or not info.get("behavioral"):
            continue
        
        logger.info(f"Attempting to check: {info['name']}")
        
        try:
            # Attempt to fetch a small sample or header
            response = requests.get(info['url'], timeout=30)
            if response.status_code == 200:
                # Try to read as CSV
                try:
                    df = pd.read_csv(pd.io.common.StringIO(response.text[:10000])) # Read header + sample
                    # If we can't read header, try full
                    if len(df.columns) < 2:
                        df = pd.read_csv(pd.io.common.StringIO(response.text))
                    
                    if validate_columns(df, info['name']):
                        valid_dataset = {
                            "key": key,
                            "name": info['name'],
                            "url": info['url'],
                            "type": info['type']
                        }
                        logger.info(f"Found valid dataset: {info['name']}")
                        break
                except Exception as e:
                    logger.warning(f"Could not parse CSV from {info['url']}: {e}")
            else:
                logger.warning(f"Failed to download {info['name']}: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error checking {info['name']}: {e}")
        except Exception as e:
            logger.warning(f"Error checking {info['name']}: {e}")

    return valid_dataset

def main():
    """Main entry point for T004."""
    logger.info("Starting data availability validation (T004)...")
    
    # 1. Check OpenNeuro ds003386 status
    ds003386_info = check_openneuro_ds003386()
    
    # 2. Search for valid behavioral datasets
    valid_dataset = check_alternative_datasets()
    
    if valid_dataset:
        logger.info(f"SUCCESS: Valid behavioral dataset found: {valid_dataset['name']}")
        logger.info(f"URL: {valid_dataset['url']}")
        logger.info("Data availability check passed. Pipeline can proceed.")
        return 0
    else:
        logger.error("ERROR: No valid behavioral dataset found containing 'confidence_rating' and 'source_label'.")
        logger.error(f"Detected source status: {ds003386_info['name']} is {ds003386_info['reason']}.")
        logger.error("Project cannot proceed without valid data.")
        logger.error("Aborting pipeline.")
        return 1

if __name__ == "__main__":
    sys.exit(main())