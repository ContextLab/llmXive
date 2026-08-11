"""
Main orchestration script for the Chess Elo Analysis Pipeline.
Orchestrates: Download -> Parse -> Process -> Model -> Validate -> Report.
"""
import sys
import logging
import argparse
from pathlib import Path
import json
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import pipeline stages from existing modules (API surface verification)
from src.data.download import download_chess_data
from src.data.parse import process_dataframe
from src.data.process import calculate_and_save_inclusion_metrics, validate_inclusion_rate
from src.models.fit import fit_beta_regression, fit_ridge_regression, save_model_metrics
from src.models.validate import run_validation_pipeline
from src.reports.generate_plots import generate_diagnostic_report
from src.validation.validate_contracts import validate_dataframe_against_contract

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
RAW_DIR = DATA_DIR / "raw"
CONFIG_DIR = DATA_DIR / "config"

# Ensure output directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def run_download_stage():
    """Executes the data download stage."""
    logger.info("Starting Download Stage...")
    try:
        # This function handles the full download pipeline including ID selection and validation
        output_path = download_chess_data()
        logger.info(f"Download stage completed. Output: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Download stage failed: {e}")
        return False

def run_processing_stage():
    """Executes the parsing and feature extraction stage."""
    logger.info("Starting Processing Stage...")
    try:
        # Process the downloaded data (streaming or batch based on implementation in parse.py)
        # Assumes download_chess_data leaves data in a standard location or returns path
        # For this orchestration, we assume process_dataframe handles the flow from raw to processed
        processed_path = process_dataframe()
        logger.info(f"Processing stage completed. Output: {processed_path}")
        return True
    except Exception as e:
        logger.error(f"Processing stage failed: {e}")
        return False

def run_modeling_stage():
    """Executes the model fitting stage."""
    logger.info("Starting Modeling Stage...")
    try:
        # Fit Beta and Ridge models
        # This function is expected to load processed data, fit models, and save metrics
        save_model_metrics() 
        logger.info("Modeling stage completed.")
        return True
    except Exception as e:
        logger.error(f"Modeling stage failed: {e}")
        return False

def run_validation_stage():
    """Executes the cross-validation stage."""
    logger.info("Starting Validation Stage...")
    try:
        run_validation_pipeline()
        logger.info("Validation stage completed.")
        return True
    except Exception as e:
        logger.error(f"Validation stage failed: {e}")
        return False

def run_reporting_stage():
    """Executes the reporting and plotting stage."""
    logger.info("Starting Reporting Stage...")
    try:
        generate_diagnostic_report()
        logger.info("Reporting stage completed.")
        return True
    except Exception as e:
        logger.error(f"Reporting stage failed: {e}")
        return False

def run_final_contract_validation():
    """
    Validates the final processed dataset against the schema.
    T018 Specific Requirement: Validate before saving final parquet.
    """
    logger.info("Running Final Contract Validation...")
    
    processed_file = PROCESSED_DIR / "games.parquet"
    schema_file = PROJECT_ROOT / "specs" / "contracts" / "game_record.schema.yaml"

    if not processed_file.exists():
        logger.error(f"Processed file not found: {processed_file}. Cannot validate.")
        return False

    if not schema_file.exists():
        logger.error(f"Schema file not found: {schema_file}. Cannot validate.")
        return False

    try:
        # Load data
        df = pd.read_parquet(processed_file)
        
        # Validate against contract
        is_valid = validate_dataframe_against_contract(df, str(schema_file))
        
        if is_valid:
            logger.info("Final contract validation PASSED.")
            return True
        else:
            logger.error("Final contract validation FAILED. Schema mismatch detected.")
            return False
    except Exception as e:
        logger.error(f"Validation process error: {e}")
        return False

def save_final_dataset():
    """
    Saves the final processed dataset to the declared path.
    T018 Requirement: Ensure data/processed/games.parquet exists.
    """
    logger.info("Saving final dataset...")
    # The processed stage (T013/T015) should have already saved this,
    # but we ensure the path is correct and the file exists as a final check.
    processed_file = PROCESSED_DIR / "games.parquet"
    if processed_file.exists():
        logger.info(f"Final dataset confirmed at: {processed_file}")
        return True
    else:
        logger.error(f"Final dataset missing at: {processed_file}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Chess Elo Analysis Pipeline")
    parser.add_argument("--sample", action="store_true", help="Run in sample mode (small dataset)")
    parser.add_argument("--config", type=str, default=None, help="Path to config file (unused in this simplified version)")
    args = parser.parse_args()

    logger.info("Pipeline started.")

    # 1. Download
    if not run_download_stage():
        logger.critical("Pipeline halted at Download Stage.")
        sys.exit(1)

    # 2. Process (Parse + Feature Extraction)
    if not run_processing_stage():
        logger.critical("Pipeline halted at Processing Stage.")
        sys.exit(1)

    # 3. Validate Final Dataset (T018 Core Requirement)
    if not run_final_contract_validation():
        logger.critical("Pipeline halted: Validation Failed.")
        sys.exit(1)

    # 4. Save Final Dataset (Ensure file exists)
    if not save_final_dataset():
        logger.critical("Pipeline halted: Final Dataset Save Failed.")
        sys.exit(1)

    # 5. Model
    if not run_modeling_stage():
        logger.critical("Pipeline halted at Modeling Stage.")
        sys.exit(1)

    # 6. Validate Models
    if not run_validation_stage():
        logger.critical("Pipeline halted at Validation Stage.")
        sys.exit(1)

    # 7. Report
    if not run_reporting_stage():
        logger.critical("Pipeline halted at Reporting Stage.")
        sys.exit(1)

    logger.info("Pipeline completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()