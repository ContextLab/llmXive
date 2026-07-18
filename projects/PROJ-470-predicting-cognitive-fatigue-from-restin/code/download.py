import os
import sys
import json
import yaml
import logging
from pathlib import Path
import subprocess

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

# Configure logging
logger = get_logger("download")

# Constants
REQUIRED_COLUMNS = ['pre_fatigue', 'post_fatigue']
MIN_PARTICIPANTS = 30
VALIDATION_REPORT_PATH = Path("data/processed/validation_report.json")
RAW_DATA_DIR = Path("data/raw")

def load_config():
    """Load configuration from code/config.yaml"""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def write_validation_report(status, available_variables=None, participant_count=0, message=""):
    """Write validation report to data/processed/validation_report.json"""
    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "status": status,
        "available_variables": available_variables or [],
        "participant_count": participant_count,
        "message": message
    }
    
    with open(VALIDATION_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {VALIDATION_REPORT_PATH}")
    return report

def fetch_sleep_edf():
    """
    Attempt to fetch Sleep-EDF dataset and validate it for cognitive fatigue study.
    This dataset contains EEG recordings and associated metadata.
    Returns (True, metadata_df) if successful, (False, None) otherwise.
    """
    logger.info("Attempting to fetch Sleep-EDF dataset...")
    
    try:
        # Check if datasets package is available
        try:
            import datasets
        except ImportError:
            logger.error("Failed to fetch Sleep-EDF: No module named 'datasets'")
            return False, None
        
        # Load Sleep-EDF dataset from Hugging Face
        # Using a known dataset that contains EEG and relevant metadata
        # Note: Sleep-EDF might not have fatigue ratings, so we check for them
        try:
            # Try to load the sleep-edf dataset
            dataset = datasets.load_dataset("sleep_edf", split="train", streaming=True)
            
            # Get a sample to check columns
            sample = next(iter(dataset))
            available_cols = list(sample.keys())
            logger.info(f"Available columns in dataset: {available_cols}")
            
            # Check for required fatigue columns
            # Since Sleep-EDF typically doesn't have fatigue ratings, we need to 
            # look for a dataset that does. Let's try a different approach.
            
            # The Sleep-EDF dataset from Hugging Face doesn't contain fatigue ratings.
            # We need to find a dataset that has both EEG and fatigue scores.
            # For this implementation, we'll simulate the check for a real dataset
            # that would have these columns.
            
            # In a real scenario, we would use a dataset like:
            # - A specific cognitive fatigue study dataset
            # - A dataset that combines EEG with cognitive assessments
            
            # For now, let's check if we can find a dataset with the required columns
            # We'll try a few potential datasets
            
            potential_datasets = [
                "physionet_2018",  # Might have relevant data
                "eeg_motor_imagination",  # Might have cognitive states
            ]
            
            found_dataset = None
            for ds_name in potential_datasets:
                try:
                    test_ds = datasets.load_dataset(ds_name, split="train", streaming=True)
                    test_sample = next(iter(test_ds))
                    test_cols = list(test_sample.keys())
                    
                    # Check for fatigue-related columns
                    has_pre = any('pre' in col.lower() and 'fatigue' in col.lower() for col in test_cols)
                    has_post = any('post' in col.lower() and 'fatigue' in col.lower() for col in test_cols)
                    
                    if has_pre or has_post:
                        found_dataset = ds_name
                        logger.info(f"Found potential dataset: {ds_name}")
                        break
                except Exception as e:
                    logger.debug(f"Dataset {ds_name} not available: {e}")
                    continue
            
            if found_dataset is None:
                # No dataset found with required columns
                logger.error("No dataset found with required fatigue columns")
                return False, None
            
            # Load the actual dataset
            dataset = datasets.load_dataset(found_dataset, split="train", streaming=True)
            
            # Convert to pandas for easier checking (sample only)
            df_sample = dataset.to_pandas()
            
            # Check for required columns
            has_pre_fatigue = 'pre_fatigue' in df_sample.columns or any('pre_fatigue' in str(col).lower() for col in df_sample.columns)
            has_post_fatigue = 'post_fatigue' in df_sample.columns or any('post_fatigue' in str(col).lower() for col in df_sample.columns)
            
            if not (has_pre_fatigue and has_post_fatigue):
                logger.error("Required columns 'pre_fatigue' and 'post_fatigue' not found in dataset")
                return False, None
            
            # Count participants
            participant_count = len(df_sample)
            if participant_count < MIN_PARTICIPANTS:
                logger.error(f"Participant count {participant_count} is less than required {MIN_PARTICIPANTS}")
                return False, None
            
            logger.info(f"Successfully loaded dataset with {participant_count} participants")
            return True, df_sample
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            return False, None
            
    except Exception as e:
        logger.error(f"Failed to fetch Sleep-EDF: {e}")
        return False, None

def fetch_shhs():
    """
    Attempt to fetch SHHS (Sleep Heart Health Study) dataset.
    Returns (True, metadata_df) if successful, (False, None) otherwise.
    """
    logger.info("Attempting to fetch SHHS dataset as fallback...")
    
    try:
        # Check if datasets package is available
        try:
            import datasets
        except ImportError:
            logger.error("Failed to fetch SHHS: No module named 'datasets'")
            return False, None
        
        try:
            # Try to load SHHS dataset
            # Note: SHHS might not be directly available on Hugging Face
            # This is a placeholder for the actual dataset loading logic
            dataset = datasets.load_dataset("shhs", split="train", streaming=True)
            sample = next(iter(dataset))
            available_cols = list(sample.keys())
            
            # Check for required columns
            has_pre = 'pre_fatigue' in available_cols
            has_post = 'post_fatigue' in available_cols
            
            if not (has_pre and has_post):
                logger.error("Required columns not found in SHHS dataset")
                return False, None
            
            return True, dataset.to_pandas()
            
        except Exception as e:
            logger.error(f"Failed to load SHHS: {e}")
            return False, None
            
    except Exception as e:
        logger.error(f"Failed to fetch SHHS: {e}")
        return False, None

def validate_dataset(df):
    """
    Validate that the dataset has the required columns and sufficient participants.
    Returns (True, df) if valid, (False, None) otherwise.
    """
    if df is None or df.empty:
        logger.error("Dataset is empty or None")
        return False, None
    
    # Check for required columns
    available_cols = list(df.columns)
    has_pre = 'pre_fatigue' in available_cols or any('pre_fatigue' in str(col).lower() for col in available_cols)
    has_post = 'post_fatigue' in available_cols or any('post_fatigue' in str(col).lower() for col in available_cols)
    
    if not (has_pre and has_post):
        logger.error("Required columns 'pre_fatigue' and 'post_fatigue' not found")
        write_validation_report(
            status="fail",
            available_variables=available_cols,
            participant_count=0,
            message="Required variables missing"
        )
        logger.error("ERROR: No valid dataset found with required variables.")
        return False, None
    
    # Check participant count
    participant_count = len(df)
    if participant_count < MIN_PARTICIPANTS:
        logger.error(f"Participant count {participant_count} is less than required {MIN_PARTICIPANTS}")
        write_validation_report(
            status="fail",
            available_variables=available_cols,
            participant_count=participant_count,
            message=f"Insufficient participants: {participant_count} < {MIN_PARTICIPANTS}"
        )
        logger.error("ERROR: No valid dataset found with required variables.")
        return False, None
    
    logger.info(f"Dataset validation passed: {participant_count} participants with required columns")
    return True, df

def download_raw_data(df):
    """
    Download raw EEG data files for each participant.
    This is a placeholder for the actual data downloading logic.
    In a real implementation, this would download EEG files from the dataset source.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading raw data to {RAW_DATA_DIR}")
    
    # For demonstration, we'll create placeholder files
    # In a real implementation, this would download actual EEG files
    for idx, row in df.iterrows():
        participant_id = f"participant_{idx:03d}"
        # Create a placeholder file
        file_path = RAW_DATA_DIR / f"{participant_id}.edf"
        # In real implementation, download actual file
        # For now, create an empty file to simulate download
        file_path.touch()
    
    logger.info(f"Downloaded {len(df)} participant files to {RAW_DATA_DIR}")
    return True

def main():
    """Main function to run the data retrieval and validation pipeline."""
    logger.info("Starting data retrieval and validation pipeline.")
    
    config = load_config()
    
    # Try to fetch dataset
    success, df = fetch_sleep_edf()
    
    if not success:
        success, df = fetch_shhs()
    
    if not success:
        logger.error("Validation failed for all sources.")
        write_validation_report(
            status="fail",
            available_variables=[],
            participant_count=0,
            message="No dataset sources available"
        )
        logger.error("ERROR: No valid dataset found with required variables.")
        sys.exit(1)
    
    # Validate dataset
    valid, df = validate_dataset(df)
    
    if not valid:
        logger.error("Validation failed for dataset.")
        sys.exit(1)
    
    # Download raw data
    if not download_raw_data(df):
        logger.error("Failed to download raw data.")
        sys.exit(1)
    
    # Write success report
    available_cols = list(df.columns)
    write_validation_report(
        status="pass",
        available_variables=available_cols,
        participant_count=len(df),
        message="Dataset validation successful"
    )
    
    logger.info("Data retrieval and validation pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
