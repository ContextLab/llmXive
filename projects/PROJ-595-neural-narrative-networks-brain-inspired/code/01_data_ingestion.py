"""
Data Ingestion Module for Neural Narrative Networks.

Handles downloading and preprocessing of external datasets including
OpenNeuro fMRI data and ROCStories corpus.
"""

import os
import sys
import json
import random
from pathlib import Path
from typing import Optional

# Import from project utilities
from utils.logging_config import get_logger, error, info, warning
from config import get_config

# Third-party imports
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install via: pip install datasets")

logger = get_logger(__name__)

# Constants
ROCSTORIES_DATASET_ID = "rocstories"
DEFAULT_SAMPLE_SIZE = 1000
OUTPUT_FILE_PATH = "data/text/rocstories_sample.jsonl"

def download_rocstories_corpus(
    output_path: Optional[str] = None,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    seed: Optional[int] = None
) -> Path:
    """
    Download ROCStories corpus from HuggingFace and sample a subset.
    
    Args:
        output_path: Path to save the JSONL file. Defaults to data/text/rocstories_sample.jsonl.
        sample_size: Number of stories to sample.
        seed: Random seed for reproducibility.
        
    Returns:
        Path to the saved JSONL file.
        
    Raises:
        RuntimeError: If download fails or data cannot be fetched.
    """
    if output_path is None:
        output_path = OUTPUT_FILE_PATH
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if seed is not None:
        random.seed(seed)
    
    logger.info(f"Attempting to download ROCStories corpus from HuggingFace (ID: {ROCSTORIES_DATASET_ID})")
    
    try:
        # Load the dataset from HuggingFace Hub
        # The rocstories dataset typically has fields: 'story', 'id' (or similar)
        dataset = load_dataset(ROCSTORIES_DATASET_ID, split="train", trust_remote_code=True)
        
        logger.info(f"Successfully loaded dataset. Total stories: {len(dataset)}")
        
        # Check if dataset has required fields
        available_columns = dataset.column_names
        logger.info(f"Available columns: {available_columns}")
        
        # Map dataset fields to expected schema
        # Common field names in rocstories: 'story', 'id', or 'input', 'output'
        story_field = None
        id_field = None
        
        for col in available_columns:
            if 'story' in col.lower():
                story_field = col
            elif 'id' in col.lower():
                id_field = col
        
        # Fallback: if no explicit 'story' field, use the first column that contains text
        if story_field is None and available_columns:
            story_field = available_columns[0]
            logger.warning(f"Could not find 'story' field. Using '{story_field}' as story field.")
        
        if story_field is None:
            raise RuntimeError("Cannot identify a story field in the dataset.")
        
        # Sample the dataset
        total_count = len(dataset)
        if sample_size > total_count:
            logger.warning(f"Sample size {sample_size} exceeds dataset size {total_count}. Using full dataset.")
            sample_size = total_count
        
        # Convert to list for sampling if not already
        dataset_list = list(dataset)
        
        # Shuffle and sample
        random.shuffle(dataset_list)
        sampled_data = dataset_list[:sample_size]
        
        # Write to JSONL with standardized schema
        with open(output_file, 'w', encoding='utf-8') as f:
            for idx, item in enumerate(sampled_data):
                record = {
                    'story': item.get(story_field, str(item)),
                    'id': item.get(id_field, idx) if id_field else idx
                }
                f.write(json.dumps(record) + '\n')
        
        logger.info(f"Successfully wrote {len(sampled_data)} stories to {output_file}")
        return output_file
        
    except Exception as e:
        error_msg = f"Failed to download or process ROCStories corpus: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def validate_ingested_data(file_path: str) -> bool:
    """
    Validate that the ingested JSONL file has the correct schema.
    
    Args:
        file_path: Path to the JSONL file to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    required_fields = {'story', 'id'}
    valid_count = 0
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if not required_fields.issubset(record.keys()):
                        logger.warning(f"Line {line_num}: Missing required fields. Found: {record.keys()}")
                        return False
                    if not isinstance(record['story'], str):
                        logger.warning(f"Line {line_num}: 'story' field is not a string.")
                        return False
                    valid_count += 1
                except json.JSONDecodeError as e:
                    logger.error(f"Line {line_num}: Invalid JSON: {e}")
                    return False
        
        logger.info(f"Validation passed: {valid_count} records validated.")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        return False

def main():
    """Main entry point for ROCStories ingestion."""
    config = get_config()
    seed = config.get('random_seed', 42)
    
    logger.info("Starting ROCStories corpus download...")
    
    try:
        output_path = download_rocstories_corpus(seed=seed)
        
        if validate_ingested_data(str(output_path)):
            logger.info("ROCStories ingestion completed successfully.")
            return 0
        else:
            logger.error("ROCStories validation failed.")
            return 1
            
    except RuntimeError as e:
        logger.error(f"ROCStories ingestion failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during ROCStories ingestion: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())