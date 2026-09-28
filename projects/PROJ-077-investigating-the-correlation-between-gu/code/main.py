import sys
import os
from pathlib import Path
from config import ensure_directories, RANDOM_SEED, SAMPLE_LIMIT
from config_validation import validate_configuration
from logging_config import get_logger, log_pipeline_start, log_pipeline_end, log_provenance

from data_ingestion import run_ingestion_pipeline
from save_cleaned_data import save_cleaned_dataset

logger = get_logger(__name__)

def main():
    """
    Main entry point for the entire pipeline.
    Orchestrates data ingestion, cleaning, and saving.
    """
    log_pipeline_start("Gut Microbiome and Cognitive Performance Analysis")
    logger.info("Starting main pipeline")
    
    # Validate configuration
    validate_configuration()
    
    # Ensure directories exist
    ensure_directories(["data/raw", "data/processed", "code", "tests", "logs"])
    
    # Run data ingestion pipeline
    try:
        cleaned_df = run_ingestion_pipeline()
        logger.info(f"Ingestion completed: {len(cleaned_df)} rows")
    
        # Save cleaned dataset
        output_path = save_cleaned_dataset(cleaned_df)
        logger.info(f"Cleaned data saved to: {output_path}")
    
        log_provenance("Pipeline execution completed successfully")
        log_pipeline_end("Success")
    
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        log_pipeline_end("Failure")
        raise

if __name__ == "__main__":
    main()