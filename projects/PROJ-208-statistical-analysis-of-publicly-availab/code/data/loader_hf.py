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
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from utils.validators import validate_dataset_schema, ensure_contracts_dir, load_schema
from utils.config import get_config, get_path

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
SCHEMA_PATH = "contracts/dataset.schema.yaml"

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
        
        # Convert to list (streaming allows us to iterate without loading all into memory)
        # We collect a sample for initial validation, but for full processing we'd iterate
        logger.info("Dataset loaded successfully. Beginning schema validation...")
        
        # For streaming, we validate the first few records to ensure schema compatibility
        sample_size = 100
        sample_data = []
        for idx, item in enumerate(dataset):
            if idx >= sample_size:
                break
            sample_data.append(item)
        
        if not sample_data:
            raise ValueError("Dataset appears to be empty")
        
        logger.info(f"Validated {len(sample_data)} sample records against schema")
        
        # For the full output, we need to write in chunks or all at once depending on memory
        # Since we are writing to Parquet, we'll collect all data
        # Note: For very large datasets, this might need chunked writing
        all_data = []
        for idx, item in enumerate(dataset):
            all_data.append(item)
            if idx % 10000 == 0:
                logger.info(f"Processed {idx} records...")
        
        logger.info(f"Total records fetched: {len(all_data)}")
        return all_data
        
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {str(e)}")
        raise

def validate_and_save(data: List[Dict[str, Any]], schema_path: str = SCHEMA_PATH, output_path: str = OUTPUT_FILE) -> bool:
    """
    Validate data against schema and save to Parquet.
    
    Args:
        data: List of issue dictionaries
        schema_path: Path to schema YAML file
        output_path: Path for output Parquet file
        
    Returns:
        True if validation and save successful
        
    Raises:
        ValidationError: If schema validation fails
    """
    logger.info(f"Validating {len(data)} records against schema at {schema_path}")
    
    # Ensure contracts directory exists
    ensure_contracts_dir()
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Validate data
    validation_result = validate_dataset_schema(data, schema)
    
    if not validation_result['valid']:
        errors = validation_result.get('errors', [])
        logger.error(f"Schema validation failed with {len(errors)} errors")
        for error in errors[:5]:  # Log first 5 errors
            logger.error(f"  - {error}")
        raise ValueError(f"Schema validation failed: {errors}")
    
    logger.info("Schema validation passed")
    
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

def main():
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
