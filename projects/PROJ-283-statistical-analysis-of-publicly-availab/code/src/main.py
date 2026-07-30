"""
Main entry point for the Chess Elo Analysis pipeline.

Orchestrates the full workflow:
1. Setup directories
2. Download raw data (if needed)
3. Parse PGNs to extract features
4. Process data (calculate probabilities, deviations)
5. Validate output against GameRecord schema
6. Save validated dataset to Parquet
"""

import sys
import logging
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import ensure_directories
from src.data.download import download_dataset
from src.data.parse import main as parse_main
from src.data.process import main as process_main
from src.validation.validate_contracts import validate_dataframe_against_contract, load_schema, SchemaValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_pipeline(sample_size: int = None, force_redownload: bool = False):
    """
    Execute the full data ingestion and validation pipeline.

    Args:
        sample_size: If provided, limits processing to this many games.
        force_redownload: If True, re-downloads the dataset.
    """
    logger.info("Starting Chess Elo Analysis Pipeline")

    # 1. Ensure directories exist
    logger.info("Ensuring directory structure...")
    ensure_directories()

    # 2. Download dataset (if needed)
    # Note: T009 handles the verification logic inside download_dataset
    raw_data_path = Path("data/raw/lichess_games.pgn")
    if force_redownload or not raw_data_path.exists():
        logger.info("Downloading dataset...")
        download_dataset()
    else:
        logger.info(f"Dataset found at {raw_data_path}, skipping download.")

    # 3. Parse PGN files
    logger.info("Parsing PGN files and extracting features...")
    parse_main(sample_size=sample_size)

    # 4. Process data (calculate Elo probabilities, deviations)
    logger.info("Processing game records...")
    process_main()

    # 5. Validate against schema
    processed_path = Path("data/processed/games.csv")
    if not processed_path.exists():
        logger.error("Processed data file not found. Pipeline stopped.")
        sys.exit(1)

    logger.info(f"Loading processed data from {processed_path}...")
    import pandas as pd
    df = pd.read_csv(processed_path)

    logger.info("Loading GameRecord schema...")
    try:
        schema = load_schema("game_record")
    except FileNotFoundError as e:
        logger.error(f"Schema file not found: {e}")
        sys.exit(1)

    logger.info("Validating dataset against GameRecord contract...")
    try:
        validate_dataframe_against_contract(df, schema)
        logger.info("Validation PASSED: Dataset conforms to GameRecord schema.")
    except SchemaValidationError as e:
        logger.error(f"Validation FAILED: {e}")
        logger.error("Aborting pipeline. Data was not saved.")
        sys.exit(1)

    # 6. Save to Parquet
    output_path = Path("data/processed/games.parquet")
    logger.info(f"Saving validated dataset to {output_path}...")
    df.to_parquet(output_path, index=False)
    logger.info(f"Pipeline completed successfully. Output saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run the Chess Elo Analysis Pipeline")
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Limit processing to N games (useful for testing)"
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download of the dataset"
    )

    args = parser.parse_args()

    try:
        run_pipeline(sample_size=args.sample, force_redownload=args.force_download)
    except Exception as e:
        logger.critical(f"Pipeline failed with critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()