"""
Data Ingestion Module for Neural Narrative Networks.
Handles downloading and preprocessing of text corpora (ROCStories).
"""
import os
import sys
import json
import random
from pathlib import Path
from typing import Optional

# Add project root to path if not already present to allow relative imports
# Note: In the actual execution environment, this is handled by the runner.
# We assume the script runs from the project root or code/ directory.
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: The 'datasets' package is required. Install it via: pip install datasets", file=sys.stderr)
    sys.exit(1)

from config import get_config
from utils.logging_config import get_logger, info, error, warning, critical

# Initialize logger
logger = get_logger(__name__)

# Configuration
CONFIG = get_config()
RANDOM_SEED = CONFIG.get('random_seed', 42)
MAX_RAM_GB = CONFIG.get('max_ram_gb', 7)

# Paths
DATA_TEXT_DIR = Path("data/text")
ROCSTORIES_OUTPUT_FILE = DATA_TEXT_DIR / "rocstories_sample.jsonl"

# ROCStories Dataset Identifier on HuggingFace
# Using the official 'rocstories' dataset which contains 10k and 2k splits.
DATASET_NAME = "rocstories"

def download_rocstories_corpus(sample_size: int = 1000, seed: int = RANDOM_SEED) -> Path:
    """
    Downloads the ROCStories corpus from HuggingFace Datasets and samples a subset.
    
    This function fetches the real dataset. If the download fails (network error,
    missing dataset, etc.), it raises an exception immediately. It does NOT
    fall back to synthetic data.
    
    Args:
        sample_size (int): Number of stories to sample.
        seed (int): Random seed for reproducibility.
        
    Returns:
        Path: Path to the saved JSONL file.
        
    Raises:
        RuntimeError: If the dataset download fails or if the sample size exceeds available data.
    """
    random.seed(seed)
    
    logger.info(f"Starting download of ROCStories corpus (dataset: {DATASET_NAME})")
    logger.info(f"Target sample size: {sample_size} stories")
    
    # Ensure output directory exists
    DATA_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load the dataset. 
        # The 'rocstories' dataset on HF typically has 'train' and 'test' splits.
        # We load the 'train' split which is the largest.
        # streaming=True is used to avoid loading the entire dataset into memory if it's large,
        # though for ROCStories (approx 10k stories) it fits in memory easily.
        # We use streaming to be safe and efficient.
        logger.info("Fetching dataset from HuggingFace...")
        dataset = load_dataset(DATASET_NAME, split="train", streaming=True)
        
        # Convert to a list to allow sampling if we need random access, 
        # but for efficiency with streaming, we can just take the first N if order doesn't matter,
        # or shuffle on the fly. 
        # To ensure a representative random sample, we'll collect the data.
        # ROCStories is small enough (~10k rows) to fit in RAM comfortably.
        
        stories_list = []
        count = 0
        logger.info("Iterating through dataset to collect stories...")
        
        # We iterate through the streaming dataset
        for item in dataset:
            if count >= sample_size:
                # If we just need the first N, we could break here. 
                # But to get a random sample, we should ideally shuffle.
                # Given the dataset is small, we'll load all or a sufficient chunk.
                # However, to be strictly compliant with "sample a representative subset",
                # we will load the whole train set if it fits, or a large chunk.
                # Let's load all train stories first to ensure randomness.
                pass 
            stories_list.append(item)
            count += 1
            
            # Safety break if we have way more than needed and don't want to load everything
            # But for ROCStories, loading 10k is fine.
            if count > 20000: 
                break
        
        logger.info(f"Loaded {len(stories_list)} stories from dataset.")
        
        if len(stories_list) < sample_size:
            logger.warning(f"Requested {sample_size} stories, but dataset only contains {len(stories_list)}. Using all available.")
            sample_size = len(stories_list)
        
        # Shuffle and sample
        random.shuffle(stories_list)
        sampled_stories = stories_list[:sample_size]
        
        logger.info(f"Sampling complete. Writing {len(sampled_stories)} stories to {ROCSTORIES_OUTPUT_FILE}")
        
        # Write to JSONL
        with open(ROCSTORIES_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for story in sampled_stories:
                # The dataset usually has 'story' or 'events' or 'title' fields.
                # rocstories format: 'story' (string), 'title' (string), 'id' (string)
                # We write the whole dict to ensure all data is preserved.
                f.write(json.dumps(story, ensure_ascii=False) + '\n')
        
        logger.info(f"Successfully saved ROCStories sample to {ROCSTORIES_OUTPUT_FILE}")
        return ROCSTORIES_OUTPUT_FILE

    except Exception as e:
        # Fail loudly: do not fallback to synthetic
        error_msg = f"CRITICAL: Failed to download ROCStories corpus from HuggingFace. Error: {str(e)}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg) from e

def validate_ingested_data(output_path: Optional[Path] = None) -> bool:
    """
    Validates that the ingested data file exists and is not empty.
    
    Args:
        output_path (Optional[Path]): Path to the JSONL file. Defaults to the standard output path.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if output_path is None:
        output_path = ROCSTORIES_OUTPUT_FILE
        
    if not output_path.exists():
        logger.error(f"Validation failed: File not found at {output_path}")
        return False
    
    if output_path.stat().st_size == 0:
        logger.error(f"Validation failed: File is empty at {output_path}")
        return False
    
    # Basic JSONL validation: check if lines are valid JSON
    valid_count = 0
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                    valid_count += 1
                except json.JSONDecodeError:
                    logger.error(f"Validation failed: Invalid JSON at line {line_num}")
                    return False
        
        logger.info(f"Validation passed: {valid_count} valid stories found in {output_path}")
        return True
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False

def main():
    """
    Main entry point for the data ingestion script.
    """
    logger.info("=== Starting ROCStories Data Ingestion ===")
    
    try:
        # Determine sample size (can be made configurable via args if needed)
        # Defaulting to 1000 as a representative subset
        sample_size = 1000
        
        output_file = download_rocstories_corpus(sample_size=sample_size)
        
        if validate_ingested_data(output_file):
            logger.info("=== Data Ingestion Completed Successfully ===")
            return 0
        else:
            logger.error("=== Data Ingestion Failed Validation ===")
            return 1
            
    except RuntimeError as e:
        logger.critical(f"=== Data Ingestion Failed: {e} ===")
        return 1
    except Exception as e:
        logger.critical(f"=== Unexpected Error: {e} ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())