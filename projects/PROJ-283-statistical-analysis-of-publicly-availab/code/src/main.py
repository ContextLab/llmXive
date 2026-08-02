"""
Main orchestration script for the Chess Elo Analysis Pipeline.

This script orchestrates the full pipeline:
1. Ensures directory structure exists.
2. Downloads/streams raw data.
3. Parses PGN games into structured records.
4. Processes records (calculates probabilities, deviations).
5. Validates the output against schema contracts.
6. Fits models and saves metrics.
7. Generates diagnostic reports.

Exit codes:
0: Success
1: Pipeline failure or validation error
"""
import sys
import logging
import argparse
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

from src.config import ensure_directories
from src.data.download import download_dataset
from src.data.parse import main as parse_main
from src.data.process import main as process_main
from src.validation.validate_contracts import validate_dataframe_against_contract, load_schema
from src.models.fit import main as fit_main
from src.models.save_metrics import main as save_metrics_main
from src.models.validate import main as validate_main
from src.reports.generate_plots import main as plots_main

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "contracts"

def run_pipeline(args):
    """Execute the full analysis pipeline."""
    logger.info("Starting Chess Elo Analysis Pipeline...")
    
    # 1. Setup directories
    logger.info("Ensuring directory structure...")
    ensure_directories()

    # 2. Download Data
    # Note: download_dataset handles its own argument parsing or defaults if not provided via CLI args
    # For T018, we assume the download step is either skipped if data exists or run with defaults
    # to ensure the pipeline is end-to-end.
    if not args.skip_download:
        logger.info("Step 1: Downloading raw data...")
        try:
            download_dataset(args.sample_size, args.output_raw)
        except Exception as e:
            logger.critical(f"Failed to download data: {e}")
            return 1
    else:
        logger.info("Skipping download step (--skip-download).")

    # 3. Parse PGN
    logger.info("Step 2: Parsing PGN games...")
    try:
        # Pass arguments to parse_main if it supports them, otherwise rely on defaults/config
        parse_main() 
    except Exception as e:
        logger.critical(f"Failed to parse PGN data: {e}")
        return 1

    # 4. Process Data (Calculate probabilities, deviations)
    logger.info("Step 3: Processing game records...")
    try:
        process_main()
    except Exception as e:
        logger.critical(f"Failed to process game records: {e}")
        return 1

    # 5. Validate Output against Contracts
    logger.info("Step 4: Validating output against schema contracts...")
    try:
        # Load the game record schema
        schema_path = SCHEMAS_DIR / "game_record.schema.yaml"
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return 1
        
        schema = load_schema(str(schema_path))
        
        # The output file path is defined in process.py (typically data/processed/games.parquet)
        # We need to load the generated data to validate it.
        # Assuming the process step outputs to data/processed/games.parquet
        input_data_path = DATA_PROCESSED_DIR / "games.parquet"
        
        if not input_data_path.exists():
            # Fallback to CSV if parquet doesn't exist but CSV does
            if (DATA_PROCESSED_DIR / "game_records.csv").exists():
                input_data_path = DATA_PROCESSED_DIR / "game_records.csv"
            else:
                raise FileNotFoundError(f"Processed data file not found: {input_data_path}")

        import pandas as pd
        if input_data_path.suffix == '.parquet':
            df = pd.read_parquet(input_data_path)
        elif input_data_path.suffix == '.csv':
            df = pd.read_csv(input_data_path)
        else:
            raise ValueError(f"Unsupported file format: {input_data_path.suffix}")

        # Validate
        validate_dataframe_against_contract(df, schema)
        logger.info("Schema validation PASSED.")
        
    except Exception as e:
        logger.critical(f"Schema validation FAILED: {e}")
        # Exit with error code 1 as per task requirement
        return 1

    # 6. Fit Models
    logger.info("Step 5: Fitting models...")
    try:
        fit_main()
    except Exception as e:
        logger.critical(f"Failed to fit models: {e}")
        return 1

    # 7. Save Metrics
    logger.info("Step 6: Saving model metrics...")
    try:
        save_metrics_main()
    except Exception as e:
        logger.critical(f"Failed to save metrics: {e}")
        return 1

    # 8. Cross-Validation
    logger.info("Step 7: Running cross-validation...")
    try:
        validate_main()
    except Exception as e:
        logger.critical(f"Failed during cross-validation: {e}")
        return 1

    # 9. Generate Plots
    logger.info("Step 8: Generating diagnostic plots...")
    try:
        plots_main()
    except Exception as e:
        logger.critical(f"Failed to generate plots: {e}")
        return 1

    logger.info("Pipeline completed successfully.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Chess Elo Analysis Pipeline")
    parser.add_argument(
        "--sample-size", 
        type=int, 
        default=1000,
        help="Number of games to sample/download (default: 1000)"
    )
    parser.add_argument(
        "--output-raw",
        type=str,
        default="data/raw/sample_games.parquet",
        help="Path for raw output file (default: data/raw/sample_games.parquet)"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip the download step if data already exists"
    )
    
    args = parser.parse_args()
    
    # Ensure output paths are relative to project root if not absolute
    if not Path(args.output_raw).is_absolute():
        args.output_raw = str(PROJECT_ROOT / args.output_raw)

    exit_code = run_pipeline(args)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
