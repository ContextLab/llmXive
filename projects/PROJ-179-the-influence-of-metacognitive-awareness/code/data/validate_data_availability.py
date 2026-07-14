"""
T004: Validate Data Availability

Checks for the existence of a VALID behavioral dataset containing
'confidence_rating' and 'source_label'.

Logic:
1. Check if OpenNeuro ds003386 is the only potential source.
   - If yes, and it lacks behavioral fields, exit with code 1.
2. Search for alternative valid datasets (local files or known URLs).
3. If a valid dataset is found, log success and exit 0.
4. If no valid dataset is found, exit 1.
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
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project root relative to this script
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DOWNLOADED_DIR = DATA_DIR / "downloaded"
DERIVED_DIR = DATA_DIR / "derived"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADED_DIR.mkdir(parents=True, exist_ok=True)
DERIVED_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_COLUMNS = ["confidence_rating", "source_label"]

# Known potential sources (URLs or local paths)
# We check local files first, then attempt to fetch known public samples
KNOWN_SOURCES = [
    # Local fallbacks that might exist if previous runs created them
    DATA_DIR / "sample_behavioral_data.csv",
    DATA_DIR / "behavioral_data.csv",
    DOWNLOADED_DIR / "sample_behavioral_data.csv",
    DOWNLOADED_DIR / "behavioral_data.csv",
    # OpenNeuro ds003386 is structural MRI, not behavioral.
    # We explicitly check for it to block the pipeline if it's the only thing.
    # We do NOT expect a local file named ds003386_behavioral.csv to exist
    # unless manually created, but we check for it to be safe.
    DATA_DIR / "ds003386_behavioral.csv",
    DOWNLOADED_DIR / "ds003386_behavioral.csv",
]

# Known public URLs for sample behavioral data (fallbacks)
FALLBACK_URLS = [
    "https://raw.githubusercontent.com/llmXive/datasets/main/sample_behavioral_data.csv",
    "https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv",
    "https://raw.githubusercontent.com/psychopy/datasets/main/behavioral_metacognition_sample.csv",
]

def check_openneuro_ds003386():
    """
    Checks if OpenNeuro ds003386 is the detected source and validates its content.
    Returns True if ds003386 is found and is the ONLY source (blocking condition),
    False if other valid sources are found or ds003386 is not present/invalid.
    """
    # ds003386 is primarily structural MRI. If a behavioral file exists, it's likely
    # a manual addition or a misnamed file. We treat it as invalid for this task.
    # We check if any file path contains 'ds003386'
    ds003386_found = False
    for path in KNOWN_SOURCES:
        if path.exists() and "ds003386" in path.name:
            ds003386_found = True
            # Try to load and check columns
            try:
                df = pd.read_csv(path)
                if all(col in df.columns for col in REQUIRED_COLUMNS):
                    # If it somehow has the columns, it's valid (unlikely for ds003386)
                    logger.info(f"Found valid behavioral data in ds003386 file: {path}")
                    return False # Not a blocking condition
                else:
                    logger.warning(f"ds003386 file found at {path} but lacks required behavioral columns.")
            except Exception as e:
                logger.warning(f"Could not read ds003386 file at {path}: {e}")

    if ds003386_found:
        logger.error("ERROR: Project blocked. OpenNeuro ds003386 lacks required behavioral fields. Aborting.")
        return True # Blocking condition met
    return False

def validate_columns(df: pd.DataFrame) -> bool:
    """Checks if the dataframe has the required columns."""
    return all(col in df.columns for col in REQUIRED_COLUMNS)

def check_alternative_datasets():
    """
    Searches for alternative valid datasets.
    Returns the path to a valid dataset if found, None otherwise.
    """
    # 1. Check local files
    for path in KNOWN_SOURCES:
        if path.exists():
            try:
                df = pd.read_csv(path)
                if validate_columns(df):
                    logger.info(f"Found valid behavioral dataset at: {path}")
                    return path
            except Exception as e:
                logger.debug(f"Could not read {path}: {e}")

    # 2. Try to download from fallback URLs
    for url in FALLBACK_URLS:
        logger.info(f"Attempting to download from: {url}")
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Save to downloaded directory
                filename = url.split("/")[-1]
                if not filename.endswith(".csv"):
                    filename = "behavioral_data.csv"
                local_path = DOWNLOADED_DIR / filename
                
                with open(local_path, "wb") as f:
                    f.write(response.content)
                
                # Validate
                df = pd.read_csv(local_path)
                if validate_columns(df):
                    logger.info(f"Successfully downloaded and validated behavioral dataset: {local_path}")
                    return local_path
                else:
                    logger.warning(f"Downloaded file {local_path} lacks required columns.")
                    local_path.unlink() # Remove invalid file
            else:
                logger.warning(f"Failed to download from {url}: {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Network error downloading from {url}: {e}")
        except Exception as e:
            logger.warning(f"Error processing {url}: {e}")

    return None

def main():
    logger.info("Starting data availability validation (T004)...")

    # Check for blocking ds003386 condition
    if check_openneuro_ds003386():
        return 1

    # Search for valid alternative datasets
    valid_path = check_alternative_datasets()

    if valid_path:
        logger.info("VALID BEHAVIORAL DATASET FOUND. Project can proceed.")
        return 0
    else:
        logger.error("ERROR: No valid behavioral dataset found. Project blocked.")
        logger.error("Please ensure a dataset with 'confidence_rating' and 'source_label' is available.")
        return 1

if __name__ == "__main__":
    sys.exit(main())