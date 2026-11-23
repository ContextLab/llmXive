"""
HuggingFace Streaming Loader for GitHub Issues Dataset.

Fetches data from 'akhousker/github-issues' using streaming mode to handle
large datasets efficiently. Validates output against the dataset schema
and saves to Parquet format.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from utils.config import get_path, get_config
from utils.validators import ensure_contracts_dir, get_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_path('logs', 'loader_hf.log'))
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_ID = "akhousker/github-issues"
STREAMING = True
OUTPUT_FILE = "data/raw/github_issues_raw_hf.parquet"
SCHEMA_NAME = "dataset_schema"

def fetch_hf_data(dataset_id: str = DATASET_ID, streaming: bool = STREAMING) -> List[Dict[str, Any]]:
    """
    Fetch GitHub issues data from HuggingFace using streaming.

    Args:
        dataset_id: HuggingFace dataset identifier
        streaming: Whether to use streaming mode

    Returns:
        List of issue dictionaries

    Raises:
        Exception: If dataset fetch fails
    """
    logger.info(f"Fetching dataset {dataset_id} in {'streaming' if streaming else 'standard'} mode")

    try:
        # Load dataset with streaming
        dataset = load_dataset(dataset_id, split="train", streaming=streaming)

        # Validate that the dataset is not empty
        first_item = next(iter(dataset), None)
        if first_item is None:
            raise ValueError("Dataset appears to be empty")

        # Since we have a streaming dataset, we will iterate over all records
        all_data = []
        for idx, item in enumerate(dataset):
            all_data.append(item)
            if idx % 10000 == 0 and idx > 0:
                logger.info(f"Processed {idx} records...")

        logger.info(f"Total records fetched: {len(all_data)}")
        return all_data

    except Exception as e:
        logger.error(f"Failed to fetch dataset: {str(e)}")
        raise

def validate_and_save(data: List[Dict[str, Any]],
                      schema_name: str = SCHEMA_NAME,
                      output_path: str = OUTPUT_FILE) -> bool:
    """
    Validate data against the contract schema and save to Parquet.

    Args:
        data: List of issue dictionaries
        schema_name: Name of the schema file (without extension) in contracts/
        output_path: Path for output Parquet file

    Returns:
        True if validation and save successful

    Raises:
        ValueError: If schema validation fails
    """
    logger.info(f"Validating {len(data)} records against schema '{schema_name}'")

    # Determine project root (two levels up from this file)
    project_root = Path(__file__).parents[2]

    # Ensure contracts directory exists
    contracts_dir = ensure_contracts_dir(project_root)

    # Obtain a validator
    validator = get_validator(project_root)

    # Validate each record
    invalid_records = []
    for idx, record in enumerate(data):
        is_valid, errors = validator.validate(record, schema_name)
        if not is_valid:
            invalid_records.append((idx, errors))

    if invalid_records:
        logger.error(f"Schema validation failed for {len(invalid_records)} records")
        for idx, errors in invalid_records[:5]:  # Log first few errors
            logger.error(f"Record {idx} errors: {errors}")
        raise ValueError(f"Schema validation failed for {len(invalid_records)} records")

    logger.info("All records passed schema validation")

    # Save to Parquet
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_parquet(output_file, index=False)
        logger.info(f"Successfully saved {len(df)} records to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save to Parquet: {str(e)}")
        raise

def main() -> bool:
    """Main entry point for the HuggingFace loader."""
    logger.info("Starting HuggingFace GitHub Issues Loader")

    try:
        # Fetch data
        data = fetch_hf_data()

        if not data:
            logger.warning("No data fetched from HuggingFace")
            return False

        # Validate and save
        success = validate_and_save(data)

        if success:
            logger.info("HuggingFace loader completed successfully")
            return True
        else:
            logger.error("HuggingFace loader failed during validation or save")
            return False

    except Exception as e:
        logger.error(f"Loader execution failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
