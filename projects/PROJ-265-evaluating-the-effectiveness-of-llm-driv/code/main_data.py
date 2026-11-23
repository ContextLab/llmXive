"""
Main data pipeline orchestrator for User Story 1.

This script orchestrates the full data pipeline:
1. Download CodeSearchNet Python dataset
2. Extract top-level functions
3. Validate syntax and imports
4. Preprocess (sanitize) code
5. Stratified sampling to produce the final dataset

Output: data/processed/functions.jsonl
"""

import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import pipeline components from existing modules
from utils.logger import (
    get_logger, 
    log_stage_start, 
    log_stage_complete, 
    log_stage_error,
    log_stage_exclusion
)
from data.download import download_codesearchnet
from data.extract import run_extraction
from data.validate import run_validation
from data.preprocess import run_preprocessing
from data.sample import run_sampling

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def run_full_pipeline(
    target_sample_size: int = 200,
    pilot_sample_size: int = 50,
    max_external_imports: int = 3
) -> bool:
    """
    Run the complete data pipeline to produce functions.jsonl.
    
    Args:
        target_sample_size: Total number of functions to sample (default 200)
        pilot_sample_size: Size of pilot sample (default 50)
        max_external_imports: Maximum allowed external imports per function (default 3)
        
    Returns:
        True if pipeline completed successfully, False otherwise
    """
    logger = get_logger(__name__)
    
    try:
        # Step 1: Download dataset
        log_stage_start(logger, "download", "Downloading CodeSearchNet Python dataset")
        download_path = download_codesearchnet(DATA_RAW_DIR)
        if not download_path or not download_path.exists():
            log_stage_error(logger, "download", "Dataset download failed or file not found")
            return False
        log_stage_complete(logger, "download", f"Dataset downloaded to {download_path}")
        
        # Step 2: Extract top-level functions
        log_stage_start(logger, "extract", "Extracting top-level functions from parquet")
        extracted_path = DATA_PROCESSED_DIR / "extracted_functions.jsonl"
        extraction_success = run_extraction(
            input_path=download_path,
            output_path=extracted_path,
            logger=logger
        )
        if not extraction_success or not extracted_path.exists():
            log_stage_error(logger, "extract", "Extraction failed or output not created")
            return False
        log_stage_complete(logger, "extract", f"Extraction complete: {extracted_path}")
        
        # Step 3: Validate functions (syntax + import limits)
        log_stage_start(logger, "validate", "Validating extracted functions")
        validated_path = DATA_PROCESSED_DIR / "validated_functions.jsonl"
        validation_success = run_validation(
            input_path=extracted_path,
            output_path=validated_path,
            max_external_imports=max_external_imports,
            logger=logger
        )
        if not validation_success or not validated_path.exists():
            log_stage_error(logger, "validate", "Validation failed or output not created")
            return False
        
        # Count validated functions
        with open(validated_path, 'r', encoding='utf-8') as f:
            validated_count = sum(1 for _ in f)
        log_stage_complete(logger, "validate", f"Validation complete: {validated_count} functions validated")
        
        # Step 4: Preprocess (sanitize) functions
        log_stage_start(logger, "preprocess", "Preprocessing (sanitizing) validated functions")
        preprocessed_path = DATA_PROCESSED_DIR / "preprocessed_functions.jsonl"
        preprocessing_success = run_preprocessing(
            input_path=validated_path,
            output_path=preprocessed_path,
            logger=logger
        )
        if not preprocessing_success or not preprocessed_path.exists():
            log_stage_error(logger, "preprocess", "Preprocessing failed or output not created")
            return False
        
        with open(preprocessed_path, 'r', encoding='utf-8') as f:
            preprocessed_count = sum(1 for _ in f)
        log_stage_complete(logger, "preprocess", f"Preprocessing complete: {preprocessed_count} functions sanitized")
        
        # Step 5: Stratified sampling
        log_stage_start(logger, "sample", f"Performing stratified sampling (target: {target_sample_size})")
        final_output_path = DATA_PROCESSED_DIR / "functions.jsonl"
        
        # First, generate the full stratified sample
        sampling_success = run_sampling(
            input_path=preprocessed_path,
            output_path=final_output_path,
            target_count=target_sample_size,
            pilot_count=pilot_sample_size,
            logger=logger
        )
        
        if not sampling_success or not final_output_path.exists():
            log_stage_error(logger, "sample", "Sampling failed or output not created")
            return False
        
        # Verify final count
        with open(final_output_path, 'r', encoding='utf-8') as f:
            final_count = sum(1 for _ in f)
        
        log_stage_complete(
            logger, 
            "sample", 
            f"Sampling complete: {final_count} functions in {final_output_path}"
        )
        
        # Generate pilot sample if not already done within run_sampling
        pilot_path = DATA_PROCESSED_DIR / "pilot_sample.jsonl"
        if not pilot_path.exists() and pilot_sample_size > 0:
            log_stage_start(logger, "pilot", f"Extracting pilot sample ({pilot_sample_size} functions)")
            # Extract first N functions as pilot (or implement proper stratified pilot logic)
            sampled_functions = []
            with open(final_output_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= pilot_sample_size:
                        break
                    sampled_functions.append(json.loads(line))
            
            with open(pilot_path, 'w', encoding='utf-8') as f:
                for func in sampled_functions:
                    f.write(json.dumps(func) + '\n')
            
            log_stage_complete(logger, "pilot", f"Pilot sample saved to {pilot_path}")
        
        return True
        
    except Exception as e:
        log_stage_error(logger, "pipeline", f"Pipeline failed with exception: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Entry point for the data pipeline orchestrator."""
    logger = get_logger(__name__)
    logger.info("Starting full data pipeline for User Story 1")
    
    success = run_full_pipeline(
        target_sample_size=200,
        pilot_sample_size=50,
        max_external_imports=3
    )
    
    if success:
        logger.info("Pipeline completed successfully")
        print(f"SUCCESS: Final dataset written to {DATA_PROCESSED_DIR / 'functions.jsonl'}")
        sys.exit(0)
    else:
        logger.error("Pipeline failed")
        print("ERROR: Pipeline failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()