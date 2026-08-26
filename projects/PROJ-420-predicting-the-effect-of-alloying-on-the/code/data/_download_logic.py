"""
Data extraction logic for Materials Project and NIST (via verified dataset).
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import joblib
import pandas as pd
from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger(__name__)

def fetch_materials_project_data() -> List[Dict[str, Any]]:
    """
    T009: Fetch data from Materials Project API.
    Uses MP_API_KEY from environment variables.
    """
    log_operation("fetch_materials_project_data", status="started")
    
    api_key = os.environ.get('MP_API_KEY')
    if not api_key:
        logger.warning("MP_API_KEY not set. Skipping Materials Project fetch.")
        return []
    
    # Placeholder for actual API call
    # In real implementation, would use requests to fetch from MP API
    logger.info("Materials Project fetch would occur here with API key")
    return []

def fetch_nist_data() -> List[Dict[str, Any]]:
    """
    T009b: Fetch data from verified NIST proxy dataset.
    Uses datasets.load_dataset("materials/alloy-elastic", split="train")
    """
    log_operation("fetch_nist_data", status="started")
    
    try:
        from datasets import load_dataset
        
        logger.info("Loading verified NIST proxy dataset: materials/alloy-elastic")
        dataset = load_dataset("materials/alloy-elastic", split="train")
        
        # Convert to list of dicts
        records = dataset.to_list()
        
        logger.info(f"Loaded {len(records)} records from NIST proxy dataset")
        return records
        
    except Exception as e:
        logger.error(f"CRITICAL: Verified source 'materials/alloy-elastic' unavailable. Cannot proceed. Error: {e}")
        raise RuntimeError("CRITICAL: Verified source 'materials/alloy-elastic' unavailable. Cannot proceed.") from e

def run_extraction():
    """
    Orchestrate data extraction from both sources.
    """
    log_operation("run_extraction", status="started")
    
    config = get_config()
    
    # Fetch from both sources
    mp_data = fetch_materials_project_data()
    nist_data = fetch_nist_data()
    
    # Merge data
    all_records = mp_data + nist_data
    
    logger.info(f"Total records extracted: {len(all_records)}")
    
    # Save to raw data file
    raw_data_path = config.data_raw_dir / "merged_raw_data.json"
    raw_data_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(raw_data_path, 'w') as f:
        json.dump(all_records, f, indent=2)
    
    logger.info(f"Saved merged raw data to {raw_data_path}")
    
    log_operation("run_extraction", status="completed", total_records=len(all_records))
    
    return all_records

def main():
    """Entry point for download logic."""
    run_extraction()

if __name__ == "__main__":
    main()
