import os
import sys
import json
import logging
import time
import io
from pathlib import Path
import yaml
import pandas as pd

def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def write_validation_report(status, details, path):
    report = {
        "status": status,
        "details": details,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

def fetch_sleep_edf_metadata():
    """
    Fetches metadata from the Sleep-EDF dataset via the Hugging Face datasets library.
    This dataset contains EEG data and often includes demographic/health metadata.
    Note: Sleep-EDF does not natively contain 'fatigue' ratings. This function
    checks for available columns and returns them. In a real pipeline, we would
    need a dataset that explicitly pairs EEG with fatigue ratings (e.g., a specific
    cognitive task dataset). For this implementation, we check the available columns
    and validate against the required fatigue columns.
    """
    try:
        from datasets import load_dataset
        # Load the dataset in streaming mode to inspect metadata without downloading full data
        # Using 'sleep_edf' dataset. If a specific fatigue dataset exists, it should be used here.
        # Since no specific fatigue dataset is universally standard in public repos without custom labels,
        # we attempt to load a known EEG dataset and check columns.
        # We use 'physionet/sleep_edf' as a proxy for EEG data structure.
        # However, per strict requirements, we must find fatigue ratings.
        # We will try to load a dataset that might have them or fail validation.
        # Attempting to load a generic EEG dataset to demonstrate the validation logic.
        # REAL SOURCE: We use the 'sleep_edf' dataset from HuggingFace as a placeholder for EEG.
        # Since it lacks fatigue, it will trigger the validation failure as per spec if fatigue is missing.
        # To satisfy the "Real Data" constraint while acknowledging the dataset limitation:
        # We will check if a specific 'fatigue' dataset exists. If not, we load Sleep-EDF and fail validation
        # because it lacks fatigue, logging the error as required.
        
        # Let's try to find a dataset that might have fatigue. 
        # There isn't a standard "Sleep-EDF with Fatigue Ratings" in public repos.
        # We will proceed by loading the Sleep-EDF metadata to check columns.
        # If the required fatigue columns are missing, we fail.
        
        ds = load_dataset("physionet/sleep_edf", split="train", streaming=True)
        # Get column names
        columns = ds.column_names
        participant_count = 0
        # Stream a few rows to count participants if possible, or rely on metadata
        # Since streaming doesn't give count immediately, we try to count unique IDs in a sample
        # or just check columns first.
        
        # Check columns for fatigue
        fatigue_columns = ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue', 
                           'post_fatigue', 'fatigue_post', 'end_fatigue']
        found_fatigue = [col for col in fatigue_columns if col in columns]
        
        # Try to count participants (approximate by sampling)
        # In a real scenario, we might have a separate metadata file.
        # Here we assume the dataset itself is the metadata source if it has participant IDs.
        unique_ids = set()
        try:
            for i, row in enumerate(ds):
                if 'subject' in row:
                    unique_ids.add(row['subject'])
                if i > 100: # Sample limit for counting
                    break
        except Exception:
            pass
        
        return {
            "participants": len(unique_ids),
            "variables": columns,
            "dataset_name": "physionet/sleep_edf"
        }
    except Exception as e:
        logging.error(f"Failed to fetch metadata: {e}")
        return {"participants": 0, "variables": [], "dataset_name": "unknown"}

def fetch_shhs_metadata():
    """
    Fetches metadata from the Sleep Heart Health Study (SHHS) if available.
    Similar to above, checks for fatigue columns.
    """
    try:
        from datasets import load_dataset
        # SHHS is not directly available as a simple 'load_dataset' in HF without specific config
        # We will simulate the check or return empty if not found.
        # For this implementation, we rely on the sleep_edf check.
        return {"participants": 0, "variables": [], "dataset_name": "shhs"}
    except Exception as e:
        return {"participants": 0, "variables": [], "dataset_name": "shhs"}

def validate_dataset(metadata):
    """
    Validates the dataset for required fatigue rating columns and sufficient participant count.
    Checks for ANY of the specified column name variations.
    """
    required_fatigue_vars = ['pre_fatigue', 'fatigue_pre', 'baseline_fatigue', 
                             'post_fatigue', 'fatigue_post', 'end_fatigue']
    
    available = metadata.get('variables', [])
    found_fatigue = [v for v in required_fatigue_vars if v in available]
    
    has_fatigue = len(found_fatigue) > 0
    n_threshold = 30 # Default from config, but we can load config here if needed
    # Load config for n_threshold
    try:
        config = load_config()
        n_threshold = config.get('n_threshold', 30)
    except:
        n_threshold = 30

    participant_count = metadata.get('participants', 0)
    
    if not has_fatigue:
        return False, available, "Required fatigue variables missing"
    if participant_count < n_threshold:
        return False, available, f"Insufficient participants: {participant_count} < {n_threshold}"
    
    return True, available, "Validation passed"

def download_raw_data(config):
    """
    Downloads the raw data to data/raw directory.
    Uses streaming or chunked download if possible, but for HF datasets, 
    we typically download the full parquet/csv if small, or stream.
    For this task, we ensure the data is present in data/raw.
    """
    from datasets import load_dataset
    import os
    
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load the dataset (sleep_edf)
    # We assume the validation passed, so we proceed.
    # Note: In a real scenario with a specific fatigue dataset, we would use that name.
    # Since Sleep-EDF doesn't have fatigue, this will technically fail validation 
    # unless a specific dataset with fatigue is provided. 
    # We will attempt to load the dataset that was validated.
    
    # For the purpose of this task, we assume the metadata check passed (hypothetically)
    # and we download the data.
    # We use 'physionet/sleep_edf' as the source.
    # To avoid downloading the whole dataset if not needed, we check if it exists.
    
    output_file = data_dir / "eeg_data.parquet"
    
    if output_file.exists():
        logging.info("Data already downloaded.")
        return
    
    try:
        # Load dataset
        # We use streaming=False to download to disk if small, or handle large datasets
        # For Sleep-EDF, it's relatively small.
        ds = load_dataset("physionet/sleep_edf", split="train")
        # Convert to parquet
        df = ds.to_pandas()
        df.to_parquet(output_file, index=False)
        logging.info(f"Data downloaded and saved to {output_file}")
    except Exception as e:
        logging.error(f"Failed to download data: {e}")
        raise

def main():
    config = load_config()
    
    # Initialize logging ensuring logs dir exists
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Ensure data/raw exists
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=logs_dir / "pipeline.log",
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )
    
    try:
        logging.info("Starting data download and validation pipeline.")
        
        # Fetch metadata (streaming or header inspection)
        # We try Sleep-EDF first
        metadata = fetch_sleep_edf_metadata()
        
        # Validate
        valid, available_vars, message = validate_dataset(metadata)
        
        if not valid:
            logging.error(f"ERROR: No valid dataset found with required variables. {message}")
            write_validation_report(
                "fail", 
                {
                    "available_variables": available_vars, 
                    "participant_count": metadata.get('participants', 0),
                    "message": message
                }, 
                logs_dir / "validation_report.json"
            )
            sys.exit(1)
        
        logging.info(f"Validation passed. Found variables: {available_vars}")
        
        # Download data
        download_raw_data(config)
        
        logging.info("Download completed successfully.")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()