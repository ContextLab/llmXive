import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils import validate_json_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_pr_data(raw_dir: str = "data/raw") -> List[Dict[str, Any]]:
    """
    Loads the raw PR data from the data/raw directory.
    Expects a file named 'pr_data.json' containing the list of processed PR objects.
    """
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_path}")
    
    # Look for the processed raw data file. 
    # Based on T012b, we expect the data to be saved here.
    # If T012b output is named differently, adjust here. 
    # Assuming the main aggregation is 'pr_data.json' or similar.
    candidates = list(raw_path.glob("pr_data*.json"))
    if not candidates:
        # Fallback to any json file if specific naming isn't established yet
        candidates = list(raw_path.glob("*.json"))
    
    if not candidates:
        raise FileNotFoundError(f"No PR data JSON files found in {raw_path}")
    
    data_file = candidates[0]
    logger.info(f"Loading raw PR data from {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected raw data to be a list, got {type(data)}")
    
    return data

def load_repo_metadata(raw_dir: str = "data/raw") -> Optional[Dict[str, Any]]:
    """
    Loads repository metadata (stars, etc.) from data/raw/repos.json
    """
    repos_path = Path(raw_dir) / "repos.json"
    if repos_path.exists():
        with open(repos_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_processed_data(pr_data: List[Dict[str, Any]], output_dir: str = "data/processed") -> None:
    """
    Saves the processed PR data to the data/processed directory.
    Validates against the pull_request schema before saving.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    schema_path = Path("contracts/pull_request.schema.yaml")
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        # Even if schema missing, we still save the data as per T018 requirement to save
    else:
        validation_count = 0
        invalid_count = 0
        for idx, record in enumerate(pr_data):
            if validate_json_schema(record, str(schema_path)):
                validation_count += 1
            else:
                invalid_count += 1
                logger.warning(f"Record {idx} failed schema validation")
        
        if invalid_count > 0:
            logger.warning(f"Validation summary: {validation_count} valid, {invalid_count} invalid out of {len(pr_data)}")
        else:
            logger.info(f"All {len(pr_data)} records passed schema validation.")

    output_file = output_path / "pr_data_processed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pr_data, f, indent=2)
    
    logger.info(f"Processed data saved to {output_file}")

def save_raw_data(pr_data: List[Dict[str, Any]], output_dir: str = "data/raw") -> None:
    """
    Saves the raw fetched PR data to the data/raw directory if not already present,
    or updates it. This ensures a persistent raw backup.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / "pr_data_raw.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pr_data, f, indent=2)
    
    logger.info(f"Raw data backup saved to {output_file}")

def main():
    """
    Main entry point for T018: Save raw and processed data with schema validation.
    """
    logger.info("Starting T018: Save raw and processed data")
    
    try:
        # Load the data that T012b/T015/T016 would have produced in memory or temp files
        # Since T012b is marked done but we need the actual data to process, 
        # we assume the pipeline flow passes data here or we load from the expected raw output.
        # For this implementation, we assume the data is available in data/raw/pr_data.json 
        # or we load the raw repos and re-fetch (which is expensive).
        # Given the constraints, we load the existing raw JSON if it exists.
        
        pr_data = load_raw_pr_data()
        logger.info(f"Loaded {len(pr_data)} PR records from raw data.")
        
        # 1. Save Raw Data (Backup/Consolidation)
        save_raw_data(pr_data)
        
        # 2. Save Processed Data (with Validation)
        save_processed_data(pr_data)
        
        logger.info("T018 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T018: {e}")
        raise

if __name__ == "__main__":
    main()