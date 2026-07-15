"""
Pipeline orchestration for data ingestion: download -> normalize -> merge.

This script orchestrates the full data ingestion workflow for predicting
plant stress response. It coordinates the download of raw data, normalization
(including LCM imputation), and identifier mapping.

Usage:
    python code/data_ingestion/pipeline.py
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import (
    DATA_RAW_PATH, 
    DATA_PROCESSED_PATH, 
    LOG_PATH, 
    LOG_LEVEL,
    REFERENCE_VALIDATOR_THRESHOLD
)
from utils.logging_config import setup_logging, get_logger
from data_ingestion.download import run_download_pipeline
from data_ingestion.normalize import run_normalization_pipeline
from data_ingestion.merge import run_merge_pipeline
from data_ingestion.sanity_check import validate_dataset_integrity
from data_ingestion.sample_check import check_sample_counts, evaluate_data_sufficiency

# Setup logging
setup_logging()
logger = get_logger("pipeline")

def log_metadata_ambiguity(record_id: str, reason: str):
    """Log records excluded due to metadata ambiguity."""
    logger.warning(f"Excluding record {record_id} due to metadata ambiguity: {reason}")

def run_pipeline():
    """
    Execute the full ingestion pipeline:
    1. Download raw data from sources defined in research.md
    2. Normalize (filter low abundance, LCM imputation)
    3. Merge (UniProt to Ensembl mapping)
    4. Validate integrity and sample counts
    
    Outputs:
        - data/processed/merged_proteomic_data.csv
        - results/pipeline_status.json
    """
    logger.info("Starting data ingestion pipeline (T014)")
    
    # Ensure output directories exist
    DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    Path("results").mkdir(exist_ok=True)
    
    pipeline_status = {
        "status": "started",
        "steps": {},
        "excluded_records": [],
        "warnings": []
    }
    
    try:
        # Step 1: Download
        logger.info("Step 1: Downloading raw data...")
        download_success, download_info = run_download_pipeline()
        
        if not download_success:
            raise RuntimeError("Download pipeline failed. Check logs for details.")
        
        pipeline_status["steps"]["download"] = {
            "success": True,
            "details": download_info
        }
        logger.info(f"Download completed. Files: {download_info.get('files_downloaded', 0)}")
        
        # Step 2: Normalize
        logger.info("Step 2: Normalizing data (filtering & LCM imputation)...")
        normalize_success, normalize_info = run_normalization_pipeline()
        
        if not normalize_success:
            raise RuntimeError("Normalization pipeline failed.")
        
        pipeline_status["steps"]["normalize"] = {
            "success": True,
            "details": normalize_info
        }
        logger.info(f"Normalization completed. Rows retained: {normalize_info.get('rows_retained', 0)}")
        
        # Step 3: Merge (Identifier Mapping)
        logger.info("Step 3: Merging datasets (UniProt -> Ensembl)...")
        merge_success, merge_info = run_merge_pipeline()
        
        if not merge_success:
            raise RuntimeError("Merge pipeline failed. Identifier mapping is critical.")
        
        pipeline_status["steps"]["merge"] = {
            "success": True,
            "details": merge_info
        }
        logger.info(f"Merge completed. Final rows: {merge_info.get('final_rows', 0)}")
        
        # Step 4: Validation & Sample Check
        logger.info("Step 4: Validating dataset integrity and sample counts...")
        
        # Run sanity check for synthetic data
        integrity_valid, integrity_details = validate_dataset_integrity()
        if not integrity_valid:
            logger.error("Dataset integrity check failed. Synthetic data detected.")
            pipeline_status["steps"]["integrity_check"] = {"success": False, "details": integrity_details}
            raise RuntimeError("Integrity check failed. Aborting pipeline.")
        
        pipeline_status["steps"]["integrity_check"] = {"success": True, "details": integrity_details}
        
        # Run sample count check
        sample_valid, sample_details = check_sample_counts()
        if not sample_valid:
            logger.warning("Sample count check failed. Insufficient samples per condition.")
            pipeline_status["steps"]["sample_check"] = {"success": False, "details": sample_details}
            # We do not abort here, but log the warning as per T037 logic
        else:
            pipeline_status["steps"]["sample_check"] = {"success": True, "details": sample_details}
        
        # Finalize status
        pipeline_status["status"] = "completed"
        pipeline_status["output_file"] = str(DATA_PROCESSED_PATH / "merged_proteomic_data.csv")
        
        # Save status report
        status_path = Path("results/pipeline_status.json")
        with open(status_path, 'w') as f:
            json.dump(pipeline_status, f, indent=2)
        
        logger.info(f"Pipeline completed successfully. Status saved to {status_path}")
        return True
        
    except Exception as e:
        pipeline_status["status"] = "failed"
        pipeline_status["error"] = str(e)
        logger.error(f"Pipeline failed: {str(e)}")
        
        # Save failure status
        status_path = Path("results/pipeline_status.json")
        with open(status_path, 'w') as f:
            json.dump(pipeline_status, f, indent=2)
        
        raise e

def main():
    """Entry point for the pipeline."""
    try:
        run_pipeline()
        print("Pipeline T014 completed successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"Pipeline T014 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()