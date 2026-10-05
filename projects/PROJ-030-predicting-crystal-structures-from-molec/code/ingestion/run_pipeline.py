"""
Main pipeline script for User Story 1: Data Ingestion and Feature Extraction.

Orchestrates the following steps:
1. Download filtered COD organic subset (T009)
2. Parse CIFs to extract SMILES and lattice parameters (T010)
3. Generate ECFP4 fingerprints (T011)
4. Handle polymorphism and build final dataset (T012)

Output: data/processed/crystal_dataset.csv
"""
import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.load_cod import stream_cod_organic
from ingestion.parse_cif import process_cif_batch
from ingestion.fingerprint import generate_fingerprints_for_dataset
from ingestion.dataset_builder import handle_polymorphism, save_dataset
from logging_config import get_logger, log_event
from config import ensure_directory

def setup_pipeline_logging():
    """Initialize logging for the pipeline."""
    logger = get_logger("pipeline")
    return logger

def run_download_and_parse(logger):
    """
    Step 1 & 2: Stream COD organic dataset and parse CIFs.
    
    Returns:
        List[Dict]: List of parsed structure dictionaries.
    """
    logger.info("Starting download and parse step...")
    log_event(logger, "pipeline_start", {"step": "download_parse"})
    
    try:
        # Stream the dataset (T009)
        cif_files = stream_cod_organic()
        
        # Parse CIFs (T010)
        parsed_data = process_cif_batch(cif_files)
        
        logger.info(f"Parsed {len(parsed_data)} CIF files successfully.")
        log_event(logger, "download_parse_complete", {"count": len(parsed_data)})
        
        return parsed_data
    except Exception as e:
        logger.error(f"Download/parse step failed: {e}", exc_info=True)
        log_event(logger, "pipeline_error", {"step": "download_parse", "error": str(e)})
        raise

def run_fingerprinting_and_finalization(parsed_data, logger):
    """
    Step 3 & 4: Generate fingerprints and handle polymorphism.
    
    Args:
        parsed_data: List of parsed structure dictionaries from previous step.
        
    Returns:
        List[Dict]: Final polymorphic dataset records.
    """
    logger.info("Starting fingerprinting and finalization step...")
    log_event(logger, "pipeline_start", {"step": "fingerprint_polymorphism"})
    
    try:
        # Generate fingerprints (T011)
        fingerprints = generate_fingerprints_for_dataset(parsed_data)
        logger.info(f"Generated fingerprints for {len(fingerprints)} molecules.")
        
        # Handle polymorphism (T012)
        polymorphic_data = handle_polymorphism(fingerprints)
        logger.info(f"Processed {len(polymorphic_data)} polymorphic records.")
        
        log_event(logger, "fingerprint_polymorphism_complete", {"count": len(polymorphic_data)})
        
        return polymorphic_data
    except Exception as e:
        logger.error(f"Fingerprinting/finalization step failed: {e}", exc_info=True)
        log_event(logger, "pipeline_error", {"step": "fingerprint_polymorphism", "error": str(e)})
        raise

def run_full_pipeline():
    """
    Execute the full ingestion pipeline end-to-end.
    
    This function orchestrates all steps defined in User Story 1:
    - T009: Download COD organic subset
    - T010: Parse CIFs
    - T011: Generate fingerprints
    - T012: Handle polymorphism
    
    Final output: data/processed/crystal_dataset.csv
    """
    logger = setup_pipeline_logging()
    logger.info("=" * 60)
    logger.info("Starting Crystal Structure Prediction Pipeline (US1)")
    logger.info("=" * 60)
    
    # Ensure output directories exist
    ensure_directory("data/processed")
    ensure_directory("data/raw")
    ensure_directory("logs")
    
    try:
        # Step 1 & 2: Download and Parse
        parsed_data = run_download_and_parse(logger)
        
        if not parsed_data:
            logger.warning("No data parsed from CIF files. Exiting.")
            log_event(logger, "pipeline_warning", {"reason": "empty_parsed_data"})
            return
        
        # Step 3 & 4: Fingerprinting and Polymorphism Handling
        polymorphic_data = run_fingerprinting_and_finalization(parsed_data, logger)
        
        if not polymorphic_data:
            logger.warning("No polymorphic records generated. Exiting.")
            log_event(logger, "pipeline_warning", {"reason": "empty_polymorphic_data"})
            return
        
        # Save final dataset (T012 output)
        output_path = "data/processed/crystal_dataset.csv"
        save_dataset(polymorphic_data, output_path)
        
        logger.info(f"Final dataset saved to: {output_path}")
        logger.info(f"Total records: {len(polymorphic_data)}")
        
        log_event(logger, "pipeline_complete", {
            "output_file": output_path,
            "record_count": len(polymorphic_data)
        })
        
        logger.info("=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        log_event(logger, "pipeline_failure", {"error": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    run_full_pipeline()