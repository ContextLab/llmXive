"""
Orchestration entry point for the simulation pipeline.
Generates synthetic data, preprocesses it, and writes final output.
"""
from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

import pandas as pd

from code.config import get_path
from code.data.simulation_mfq import main as run_mfq_simulation
from code.data.simulation_stories import main as run_stories_simulation
from code.data.ingest import main as run_ingestion
from code.data.preprocess import main as run_preprocessing
from code.utils.hashing import checksum_derived_datasets, update_state_file
from code.utils.logging import log_operation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_path("data/logs/simulation.log"))
    ]
)
logger = logging.getLogger(__name__)


def log_pipeline_step(operation: str, status: str = "START", details: Optional[str] = None) -> None:
    """Log a pipeline step with operation, status, and optional details."""
    log_operation(operation, status=status, details=details)


def run_simulation_pipeline() -> None:
    """Execute the full simulation pipeline."""
    log_pipeline_step("START_SIMULATION", "START", "Beginning simulation pipeline")
    
    # Step 1: Generate synthetic MFQ data
    log_pipeline_step("MFQ_GENERATION", "START", "Generating synthetic MFQ data")
    try:
        run_mfq_simulation()
        log_pipeline_step("MFQ_GENERATION", "COMPLETE", "MFQ generation completed")
    except Exception as e:
        log_pipeline_step("MFQ_GENERATION", "FAILED", str(e))
        raise
    
    # Step 2: Generate synthetic stories and VR logs
    log_pipeline_step("STORIES_GENERATION", "START", "Generating synthetic stories and VR logs")
    try:
        run_stories_simulation()
        log_pipeline_step("STORIES_GENERATION", "COMPLETE", "Stories generation completed")
    except Exception as e:
        log_pipeline_step("STORIES_GENERATION", "FAILED", str(e))
        raise
    
    # Step 3: Ingest and merge datasets
    log_pipeline_step("INGESTION", "START", "Ingesting and merging datasets")
    try:
        run_ingestion()
        log_pipeline_step("INGESTION", "COMPLETE", "Ingestion completed")
    except Exception as e:
        log_pipeline_step("INGESTION", "FAILED", str(e))
        raise
    
    # Step 4: Preprocess data
    log_pipeline_step("PREPROCESSING", "START", "Preprocessing merged data")
    try:
        run_preprocessing()
        log_pipeline_step("PREPROCESSING", "COMPLETE", "Preprocessing completed")
    except Exception as e:
        log_pipeline_step("PREPROCESSING", "FAILED", str(e))
        raise
    
    log_pipeline_step("END_SIMULATION", "COMPLETE", "Simulation pipeline completed successfully")


def write_final_output(df: pd.DataFrame, output_path: str) -> None:
    """Write the final processed data to the specified output path."""
    full_path = get_path(output_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing final output to {full_path}")
    df.to_csv(full_path, index=False)
    logger.info(f"Successfully wrote {len(df)} records to {full_path}")


def update_hashes() -> None:
    """Update artifact hashes for all derived datasets."""
    checksum_derived_datasets()


def main() -> None:
    """Main entry point for the simulation script."""
    try:
        # Run the pipeline
        run_simulation_pipeline()
        
        # Write final aggregated output if needed
        # Note: The pipeline steps already write their own outputs
        # This is a final aggregation if required by the run-book
        output_path = get_path("data/processed/simulated_data.csv")
        
        # If the preprocess step already wrote to preprocessed_data.csv,
        # we can copy or aggregate it here. For now, we ensure the file exists
        # by checking if the pipeline produced it.
        if not output_path.exists():
            # Fallback: use the preprocessed output as the simulated data
            preprocessed_path = get_path("data/processed/preprocessed_data.csv")
            if preprocessed_path.exists():
                import shutil
                shutil.copy(preprocessed_path, output_path)
                logger.info(f"Copied preprocessed data to {output_path}")
            else:
                logger.warning("No final output file found. Pipeline may have failed silently.")
        
        # Update hashes
        update_hashes()
        
    except Exception as e:
        logger.error(f"Simulation pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
