import sys
import logging
import argparse
from pathlib import Path
import json

# Import specific functions from sibling modules based on the provided API surface
from src.data.download import main as download_main
from src.data.parse import main as parse_main, calculate_and_save_inclusion_metrics, validate_inclusion_rate
from src.data.process import main as process_main
from src.models.fit import main as fit_main, save_model_metrics
from src.models.validate import main as validate_main
from src.reports.generate_plots import main as plots_main
from src.validation.validate_contracts import main as validate_contracts_main
from src.config import ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_download_stage():
    logger.info("Starting Download Stage...")
    # The download script handles its own argument parsing and execution
    # We invoke it via its main function but need to ensure it runs correctly
    # Since download.py has its own argparse, we might need to pass sys.argv or mock it
    # However, to keep it simple and robust, we assume the environment is set up
    # or we call the logic directly if possible.
    # Given the constraints, we will try to call the main logic.
    # Note: download.py's main() expects command line args. We'll let it handle sys.argv.
    try:
        download_main()
        logger.info("Download stage completed successfully.")
        return True
    except SystemExit as e:
        if e.code != 0:
            logger.error("Download stage failed.")
            return False
        return True
    except Exception as e:
        logger.error(f"Download stage failed with exception: {e}")
        return False

def run_processing_stage():
    logger.info("Starting Processing Stage...")
    try:
        # parse_main handles PGN parsing and feature extraction
        parse_main()
        # process_main handles outcome deviation calculation and inclusion metrics
        process_main()
        logger.info("Processing stage completed successfully.")
        return True
    except SystemExit as e:
        if e.code != 0:
            logger.error("Processing stage failed.")
            return False
        return True
    except Exception as e:
        logger.error(f"Processing stage failed with exception: {e}")
        return False

def run_modeling_stage():
    logger.info("Starting Modeling Stage...")
    try:
        # fit_main handles model fitting and saving metrics
        fit_main()
        logger.info("Modeling stage completed successfully.")
        return True
    except SystemExit as e:
        if e.code != 0:
            logger.error("Modeling stage failed.")
            return False
        return True
    except Exception as e:
        logger.error(f"Modeling stage failed with exception: {e}")
        return False

def run_validation_stage():
    logger.info("Starting Validation Stage...")
    try:
        # validate_main handles cross-validation
        validate_main()
        logger.info("Validation stage completed successfully.")
        return True
    except SystemExit as e:
        if e.code != 0:
            logger.error("Validation stage failed.")
            return False
        return True
    except Exception as e:
        logger.error(f"Validation stage failed with exception: {e}")
        return False

def run_reporting_stage():
    logger.info("Starting Reporting Stage...")
    try:
        # plots_main handles plot generation and diagnostic report
        plots_main()
        logger.info("Reporting stage completed successfully.")
        return True
    except SystemExit as e:
        if e.code != 0:
            logger.error("Reporting stage failed.")
            return False
        return True
    except Exception as e:
        logger.error(f"Reporting stage failed with exception: {e}")
        return False

def run_final_contract_validation():
    """
    Validates the final processed dataset against the GameRecord schema.
    This is the critical step for T018 to ensure data integrity before saving.
    """
    logger.info("Running Final Contract Validation...")
    try:
        # We need to invoke the validation logic.
        # The validate_contracts.py script has its own argparse.
        # We will construct the arguments programmatically to ensure it runs correctly.
        # The expected arguments are: --data <path> [--contracts <path>] [--format <format>]
        # Based on T018 requirements, we validate data/processed/games.parquet (or csv if that's the intermediate)
        # The task says: "calling validate_contracts.py on the generated dataset before saving to data/processed/games.parquet"
        # Assuming the process stage outputs a parquet file or we save it here.
        
        # Let's assume the processed data is at data/processed/game_records.parquet (common convention)
        # Or we check what process_main produces. The task says "before saving to data/processed/games.parquet"
        # So we validate the intermediate file, then save the final one.
        
        input_file = Path("data/processed/game_records.parquet")
        if not input_file.exists():
            input_file = Path("data/processed/game_records.csv") # Fallback
        
        if not input_file.exists():
            logger.error(f"Input file for validation not found: {input_file}")
            return False

        # We will simulate the CLI call by setting sys.argv and calling main
        original_argv = sys.argv
        sys.argv = [
            "validate_contracts.py",
            "--data", str(input_file),
            "--contracts", "specs/contracts/game_record.schema.yaml",
            "--format", "parquet"
        ]
        
        validate_contracts_main()
        
        # Restore argv
        sys.argv = original_argv
        
        logger.info("Contract validation passed.")
        return True
    except SystemExit as e:
        sys.argv = original_argv
        if e.code != 0:
            logger.error("Contract validation failed.")
            return False
        return True
    except Exception as e:
        sys.argv = original_argv
        logger.error(f"Contract validation failed with exception: {e}")
        return False

def save_final_dataset():
    """
    Saves the validated dataset to data/processed/games.parquet.
    """
    logger.info("Saving final dataset to data/processed/games.parquet...")
    try:
        # We need to load the validated data and save it as 'games.parquet'
        # The process stage likely outputs 'game_records.parquet' or similar.
        # We assume the validation passed, so the data exists.
        import pandas as pd
        
        input_file = Path("data/processed/game_records.parquet")
        if not input_file.exists():
            input_file = Path("data/processed/game_records.csv")
        
        if input_file.suffix == '.parquet':
            df = pd.read_parquet(input_file)
        else:
            df = pd.read_csv(input_file)
        
        output_file = Path("data/processed/games.parquet")
        df.to_parquet(output_file, index=False)
        
        logger.info(f"Final dataset saved to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save final dataset: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Chess Elo Analysis Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--skip-download", action="store_true", help="Skip download stage")
    parser.add_argument("--skip-processing", action="store_true", help="Skip processing stage")
    parser.add_argument("--skip-modeling", action="store_true", help="Skip modeling stage")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation stage")
    parser.add_argument("--skip-reporting", action="store_true", help="Skip reporting stage")
    
    args = parser.parse_args()
    
    ensure_directories()
    
    success = True
    
    if not args.skip_download:
        if not run_download_stage():
            success = False
    
    if success and not args.skip_processing:
        if not run_processing_stage():
            success = False
    
    if success and not args.skip_modeling:
        if not run_modeling_stage():
            success = False
    
    if success and not args.skip_validation:
        if not run_validation_stage():
            success = False
    
    if success and not args.skip_reporting:
        if not run_reporting_stage():
            success = False
    
    # Final Contract Validation (T018 Requirement)
    if success:
        if not run_final_contract_validation():
            success = False
    
    # Save Final Dataset (T018 Requirement)
    if success:
        if not save_final_dataset():
            success = False
    
    if success:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
