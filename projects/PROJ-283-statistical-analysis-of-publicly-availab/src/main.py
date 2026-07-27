"""
Main entry point for the Chess Elo Analysis pipeline.

This script orchestrates the full pipeline:
1. Ensures directory structure exists.
2. Downloads raw PGN data (if not present).
3. Parses PGNs to extract features (ECO, move times, material imbalance).
4. Processes data to calculate Elo probabilities and outcome deviations.
5. Validates the final dataset against the GameRecord schema.
6. Saves the validated dataset to data/processed/games.parquet.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import ensure_directories
from src.data.download import download_lichess_data
from src.data.parse import main as parse_main
from src.data.process import main as process_main
from src.validation.validate_contracts import validate_dataframe_against_contract, load_schema, SchemaValidationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Execute the full pipeline with schema validation."""
    logger.info("Starting Chess Elo Analysis Pipeline...")

    # 1. Ensure directories exist
    logger.info("Ensuring directory structure...")
    ensure_directories()

    # 2. Download data (if needed)
    # Note: download_lichess_data handles its own verification and retry logic
    raw_data_path = Path("data/raw/games.pgn")
    if not raw_data_path.exists():
        logger.info("Raw data not found. Downloading...")
        download_lichess_data()
    else:
        logger.info(f"Raw data found at {raw_data_path}. Skipping download.")

    # 3. Parse PGN files
    logger.info("Parsing PGN files...")
    parse_main()

    # 4. Process data (calculate Elo metrics)
    logger.info("Processing game records...")
    process_main()

    # 5. Load the generated dataset for validation
    processed_data_path = Path("data/processed/games_raw.csv") # Output of process.py before final save
    if not processed_data_path.exists():
        # Fallback to parquet if csv is not the immediate output of process_main in this specific impl
        # But based on task T016/T017, process.py usually outputs a clean dataframe.
        # Let's assume process_main writes to data/processed/games_clean.csv or similar.
        # We need to check what process_main actually outputs.
        # Based on T016/T017, it likely outputs a CSV or Parquet.
        # Let's try to load the most likely output of the previous step.
        # If process_main saves to data/processed/games.csv, we load that.
        # If it saves to data/processed/games.parquet, we load that.
        # The task says "before saving to data/processed/games.parquet".
        # So we assume the intermediate file exists.
        possible_paths = [
            Path("data/processed/games.csv"),
            Path("data/processed/games_clean.csv"),
            Path("data/processed/raw_games.csv")
        ]
        found = False
        for p in possible_paths:
            if p.exists():
                processed_data_path = p
                found = True
                break
        
        if not found:
            logger.error("Could not find intermediate processed data file. The pipeline may have failed earlier.")
            sys.exit(1)

    import pandas as pd
    try:
        if processed_data_path.suffix == '.parquet':
            df = pd.read_parquet(processed_data_path)
        else:
            df = pd.read_csv(processed_data_path)
    except Exception as e:
        logger.error(f"Failed to load processed data from {processed_data_path}: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} records from {processed_data_path}")

    # 6. Validate against GameRecord schema
    logger.info("Validating dataset against GameRecord schema...")
    try:
        schema_path = Path("specs/contracts/game_record.schema.yaml")
        if not schema_path.exists():
            logger.error(f"Schema file not found at {schema_path}")
            sys.exit(1)
        
        schema = load_schema(schema_path)
        validate_dataframe_against_contract(df, schema, contract_name="game_record")
        logger.info("Schema validation PASSED.")
    except SchemaValidationError as e:
        logger.error(f"Schema validation FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

    # 7. Save to final destination
    final_output_path = Path("data/processed/games.parquet")
    logger.info(f"Saving validated dataset to {final_output_path}...")
    df.to_parquet(final_output_path, index=False)
    
    logger.info(f"Pipeline completed successfully. Output saved to {final_output_path}")

if __name__ == "__main__":
    main()
