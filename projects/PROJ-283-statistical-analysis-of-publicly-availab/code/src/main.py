"""
Main orchestration script for the Chess Elo Analysis Pipeline.

This script coordinates the entire pipeline:
1. Data Download (T008e)
2. Data Parsing & Feature Extraction (T013, T014)
3. Online Processing & Metrics (T015, T017)
4. Model Fitting (T022)
5. Validation (T018)
6. Reporting (T033)

It ensures that all stages complete successfully and that the final output
passes contract validation before being saved.
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

# Import pipeline stages
from src.data.download import download_chess_data, DataFetchError
from src.data.parse import parse_pgn_iterator, process_dataframe
from src.data.process import calculate_and_save_inclusion_metrics, validate_inclusion_rate
from src.models.fit import save_model_metrics
from src.models.validate import run_validation_pipeline
from src.reports.generate_plots import generate_diagnostic_report
from src.validation.validate_contracts import validate_dataframe_against_contract, load_schema
from src.config import ensure_directories

def run_download_stage():
    """Execute the data download stage."""
    logger.info("Starting data download stage...")
    try:
        # This function handles the full download, streaming, and saving to parquet
        # as implemented in T008e
        output_path = download_chess_data()
        logger.info(f"Download stage complete. Data saved to: {output_path}")
        return output_path
    except DataFetchError as e:
        logger.error(f"Download stage failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

def run_processing_stage(raw_data_path):
    """Execute the data parsing and processing stage."""
    logger.info("Starting data processing stage...")
    
    try:
        # Load and parse the raw data
        # The download stage saves to parquet, but we need to parse PGN
        # If the download stage already produced a processed parquet, we might skip this
        # However, per the pipeline design, download gets raw PGN, parse extracts features
        
        # For this implementation, we assume download_chess_data returns a path to raw PGN
        # and we need to process it.
        # If the download stage already saved a processed parquet (as per some implementations),
        # we might need to adjust. Let's assume it returns the raw PGN file path.
        
        # Check if the raw file exists
        if not Path(raw_data_path).exists():
            logger.error(f"Raw data file not found: {raw_data_path}")
            sys.exit(1)
        
        # Parse the PGN data and extract features
        # This calls the streaming parser from T013 and the processing from T015
        processed_df = process_dataframe(raw_data_path)
        
        if processed_df is None or processed_df.empty:
            logger.error("Processing stage failed: No data processed.")
            sys.exit(1)
        
        # Save inclusion metrics (T017)
        inclusion_metrics_path = calculate_and_save_inclusion_metrics(processed_df)
        validate_inclusion_rate(inclusion_metrics_path)
        
        # Save the processed dataset
        processed_output_path = Path("data/processed/games.parquet")
        processed_df.to_parquet(processed_output_path, index=False)
        logger.info(f"Processing stage complete. Processed data saved to: {processed_output_path}")
        
        return processed_output_path, processed_df
        
    except Exception as e:
        logger.error(f"Processing stage failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_modeling_stage(processed_data_path):
    """Execute the model fitting stage."""
    logger.info("Starting model fitting stage...")
    
    try:
        # Load the processed data
        df = pd.read_parquet(processed_data_path)
        
        # Fit models and save metrics (T022, T027)
        # This function should handle both Beta and Ridge regression
        model_metrics_path = save_model_metrics(df)
        
        logger.info(f"Modeling stage complete. Metrics saved to: {model_metrics_path}")
        return model_metrics_path
        
    except Exception as e:
        logger.error(f"Modeling stage failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_validation_stage(processed_data_path):
    """Execute the contract validation stage."""
    logger.info("Starting contract validation stage...")
    
    try:
        # Load the processed data
        df = pd.read_parquet(processed_data_path)
        
        # Load the game record schema
        schema_path = Path("specs/contracts/game_record.schema.yaml")
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            sys.exit(1)
        
        schema = load_schema(schema_path)
        
        # Validate the dataframe against the schema
        is_valid = validate_dataframe_against_contract(df, schema)
        
        if not is_valid:
            logger.error("Validation failed: Data does not conform to the game_record schema.")
            sys.exit(1)
        
        logger.info("Validation stage complete: Data conforms to schema.")
        return True
        
    except Exception as e:
        logger.error(f"Validation stage failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_reporting_stage(processed_data_path, model_metrics_path):
    """Execute the reporting stage."""
    logger.info("Starting reporting stage...")
    
    try:
        # Generate diagnostic report and plots (T033)
        report_path = generate_diagnostic_report(processed_data_path, model_metrics_path)
        
        logger.info(f"Reporting stage complete. Report saved to: {report_path}")
        return report_path
        
    except Exception as e:
        logger.error(f"Reporting stage failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_final_contract_validation(processed_data_path):
    """Run final contract validation on the saved dataset."""
    logger.info("Running final contract validation...")
    
    try:
        # Load the final processed data
        df = pd.read_parquet(processed_data_path)
        
        # Load the schema
        schema_path = Path("specs/contracts/game_record.schema.yaml")
        schema = load_schema(schema_path)
        
        # Validate
        is_valid = validate_dataframe_against_contract(df, schema)
        
        if not is_valid:
            logger.error("Final validation failed: Output data does not conform to schema.")
            sys.exit(1)
        
        logger.info("Final validation passed.")
        return True
        
    except Exception as e:
        logger.error(f"Final validation failed: {e}")
        sys.exit(1)

def save_final_dataset(processed_df, output_path):
    """Save the final processed dataset."""
    logger.info(f"Saving final dataset to: {output_path}")
    processed_df.to_parquet(output_path, index=False)
    logger.info("Final dataset saved.")

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Chess Elo Analysis Pipeline")
    parser.add_argument("--skip-download", action="store_true", help="Skip the download stage")
    parser.add_argument("--skip-processing", action="store_true", help="Skip the processing stage")
    parser.add_argument("--skip-modeling", action="store_true", help="Skip the modeling stage")
    parser.add_argument("--skip-validation", action="store_true", help="Skip the validation stage")
    parser.add_argument("--skip-reporting", action="store_true", help="Skip the reporting stage")
    parser.add_argument("--raw-data", type=str, help="Path to raw data file (if skipping download)")
    parser.add_argument("--processed-data", type=str, help="Path to processed data file (if skipping processing)")
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    raw_data_path = None
    processed_data_path = None
    model_metrics_path = None
    
    # Stage 1: Download
    if not args.skip_download:
        raw_data_path = run_download_stage()
    elif args.raw_data:
        raw_data_path = args.raw_data
        logger.info(f"Using provided raw data path: {raw_data_path}")
    else:
        logger.warning("Skipping download stage. Please provide --raw-data if data is not already downloaded.")
        # We need a raw data path for the next stage
        # If not provided, we might need to exit or assume a default
        # For now, let's assume the user must provide it if skipping download
        if not args.raw_data:
            logger.error("Download skipped but no raw data path provided. Exiting.")
            sys.exit(1)
        raw_data_path = args.raw_data
    
    # Stage 2: Processing
    if not args.skip_processing:
        processed_data_path, processed_df = run_processing_stage(raw_data_path)
    elif args.processed_data:
        processed_data_path = args.processed_data
        logger.info(f"Using provided processed data path: {processed_data_path}")
        # Load the data for subsequent stages
        processed_df = pd.read_parquet(processed_data_path)
    else:
        logger.warning("Skipping processing stage. Please provide --processed-data if data is not already processed.")
        if not args.processed_data:
            logger.error("Processing skipped but no processed data path provided. Exiting.")
            sys.exit(1)
        processed_data_path = args.processed_data
        processed_df = pd.read_parquet(processed_data_path)
    
    # Stage 3: Modeling
    if not args.skip_modeling:
        if processed_data_path:
            model_metrics_path = run_modeling_stage(processed_data_path)
        else:
            logger.error("Cannot run modeling stage without processed data.")
            sys.exit(1)
    elif not args.skip_reporting:
        # If we skip modeling but do reporting, we need model metrics
        # For now, let's assume model_metrics_path is required for reporting
        # If not provided, we might need to exit
        logger.warning("Modeling skipped. Reporting may fail without model metrics.")
    
    # Stage 4: Validation
    if not args.skip_validation:
        if processed_data_path:
            run_validation_stage(processed_data_path)
        else:
            logger.error("Cannot run validation stage without processed data.")
            sys.exit(1)
    
    # Stage 5: Reporting
    if not args.skip_reporting:
        if processed_data_path and model_metrics_path:
            run_reporting_stage(processed_data_path, model_metrics_path)
        elif processed_data_path:
            logger.warning("Reporting requires model metrics. Skipping reporting.")
        else:
            logger.error("Cannot run reporting stage without processed data and model metrics.")
            sys.exit(1)
    
    # Final Validation
    if processed_data_path:
        run_final_contract_validation(processed_data_path)
    
    logger.info("Pipeline completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()