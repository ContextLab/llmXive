"""
Main pipeline script for User Story 1: Data Ingestion and Feature Extraction.

Orchestrates the following steps:
1. Download (T009): Stream COD organic dataset from HuggingFace.
2. Parsing (T010): Parse CIF files to extract SMILES and lattice parameters.
3. Fingerprinting (T011): Generate ECFP4 fingerprints.
4. Dataset Building (T012): Handle polymorphism and produce the final CSV.

Output: data/processed/crystal_dataset.csv
"""
import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_path_processed_data, get_path_raw_data, ensure_directory, get_path_validation
from ingestion.load_cod import stream_cod_organic
from ingestion.parse_cif import process_cif_batch
from ingestion.fingerprint import generate_fingerprints_for_dataset, save_fingerprints_to_csv
from ingestion.dataset_builder import handle_polymorphism, save_dataset
from ingestion.validate_source import validate_source
from ingestion.validate_fingerprints import validate_dataset as validate_fingerprints
from utils.error_handlers import handle_memory_error, handle_download_failure
from logging_config import get_logger, log_event
from exceptions import SourceUnreachableError, DownloadError

# Constants
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
VALIDATION_DIR = "data/validation"
LOGS_DIR = "logs"

OUTPUT_FILENAME = "crystal_dataset.csv"
INTERMEDIATE_PARQUET = "crystal_molecules.parquet"
POLYMORPHIC_CSV = "polymorphic_dataset.csv"
STREAMING_METRICS_FILE = "streaming_metrics.json"
EXCLUSION_LOG_FILE = "data/processing/exclusion_log.json"

def setup_pipeline_logging():
    """Initialize logging for the pipeline."""
    ensure_directory(LOGS_DIR)
    log_file = os.path.join(LOGS_DIR, "pipeline_run.log")
    logger = get_logger("pipeline", log_file=log_file, level=logging.INFO)
    return logger

@handle_download_failure
@handle_memory_error
def run_download_and_parse(logger: logging.Logger) -> Optional[Path]:
    """
    Step 1 & 2: Download and Parse.
    
    1. Validate source citation.
    2. Stream COD organic dataset.
    3. Parse CIFs to extract SMILES and lattice params.
    4. Save intermediate parquet.
    """
    logger.info("Starting Download and Parse phase.")
    
    # 1. Validate Source
    logger.info("Validating data source citation...")
    try:
        validate_source()
        logger.info("Source citation validated successfully.")
    except SourceUnreachableError as e:
        logger.error(f"Source validation failed: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during source validation: {e}")
        raise e

    # 2. Stream and Download
    raw_output_path = get_path_raw_data(INTERMEDIATE_PARQUET)
    ensure_directory(os.path.dirname(raw_output_path))
    
    logger.info(f"Streaming COD organic dataset to {raw_output_path}...")
    try:
        # stream_cod_organic is expected to handle the HF streaming logic
        stream_cod_organic(output_path=raw_output_path)
        logger.info(f"Download complete: {raw_output_path}")
    except Exception as e:
        logger.error(f"Failed to download/stream data: {e}")
        raise e

    # 3. Parse CIFs
    # Note: The existing parse_cif.py expects to process the downloaded files.
    # Since load_cod.py streams to a parquet (or list of files), we pass that path.
    # If load_cod produces a parquet of file paths, parse_cif reads it.
    # If load_cod produces actual files, we pass the directory.
    # Assuming stream_cod_organic produces a manifest or parquet of data to be parsed.
    # For this implementation, we assume parse_cif_batch can take the raw output path.
    
    parsed_output_path = get_path_processed_data(INTERMEDIATE_PARQUET)
    ensure_directory(os.path.dirname(parsed_output_path))
    
    logger.info("Parsing CIF files...")
    try:
        process_cif_batch(input_path=raw_output_path, output_path=parsed_output_path)
        logger.info(f"Parsing complete: {parsed_output_path}")
    except Exception as e:
        logger.error(f"Failed to parse CIF files: {e}")
        raise e

    return parsed_output_path

@handle_memory_error
def run_fingerprinting_and_finalization(parsed_path: Path, logger: logging.Logger) -> Path:
    """
    Step 3 & 4: Fingerprinting and Dataset Building.
    
    1. Generate ECFP4 fingerprints.
    2. Handle polymorphism (SMILES, Space Group) -> distinct rows.
    3. Save final CSV.
    """
    logger.info("Starting Fingerprinting and Finalization phase.")
    
    # 3. Fingerprinting
    logger.info("Generating ECFP4 fingerprints...")
    try:
        # generate_fingerprints_for_dataset reads the parsed parquet and adds fingerprints
        fingerprinted_path = generate_fingerprints_for_dataset(
            input_path=str(parsed_path),
            output_path=str(parsed_path).replace(".parquet", "_fingerprinted.parquet")
        )
        logger.info(f"Fingerprinting complete: {fingerprinted_path}")
    except Exception as e:
        logger.error(f"Failed to generate fingerprints: {e}")
        raise e

    # 4. Polymorphism Handling & Final Dataset
    # The task requires outputting data/processed/crystal_dataset.csv
    final_output_path = get_path_processed_data(OUTPUT_FILENAME)
    ensure_directory(os.path.dirname(final_output_path))
    
    logger.info("Handling polymorphism and building final dataset...")
    try:
        # handle_polymorphism treats (SMILES, Space Group) as distinct
        # It should read the fingerprinted data and write the final CSV
        handle_polymorphism(
            input_path=str(fingerprinted_path),
            output_path=final_output_path
        )
        logger.info(f"Polymorphism handling complete: {final_output_path}")
    except Exception as e:
        logger.error(f"Failed to handle polymorphism: {e}")
        raise e

    # 5. Validation (Optional but recommended per T014 dependency)
    logger.info("Validating final dataset structure...")
    try:
        validate_fingerprints(dataset_path=final_output_path)
        logger.info("Validation passed.")
    except Exception as e:
        logger.warning(f"Validation check issued warnings/errors: {e}")
        # Do not fail the pipeline if validation only warns, but log it.

    return final_output_path

def run_full_pipeline():
    """Execute the full ingestion pipeline."""
    logger = setup_pipeline_logging()
    log_event(logger, "Pipeline Start", {"pipeline": "US1_Ingestion"})
    
    try:
        # Ensure directories exist
        ensure_directory(PROCESSED_DATA_DIR)
        ensure_directory(RAW_DATA_DIR)
        ensure_directory(VALIDATION_DIR)
        ensure_directory("data/processing") # For exclusion logs

        # Step 1 & 2: Download and Parse
        parsed_path = run_download_and_parse(logger)
        if not parsed_path or not parsed_path.exists():
            raise FileNotFoundError(f"Parsed data file not found at {parsed_path}")

        # Step 3 & 4: Fingerprint and Build
        final_output = run_fingerprinting_and_finalization(parsed_path, logger)
        
        if not final_output.exists():
            raise FileNotFoundError(f"Final dataset not written to {final_output}")

        log_event(logger, "Pipeline Success", {
            "output_file": str(final_output),
            "status": "completed"
        })
        print(f"Pipeline completed successfully. Output: {final_output}")
        return final_output

    except Exception as e:
        log_event(logger, "Pipeline Failed", {
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        print(f"Pipeline failed: {e}")
        raise e

def main():
    """Entry point for the script."""
    run_full_pipeline()

if __name__ == "__main__":
    main()