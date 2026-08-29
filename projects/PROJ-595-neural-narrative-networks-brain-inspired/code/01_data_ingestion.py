"""
Data Ingestion Module for Neural Narrative Networks.
Handles downloading and preprocessing of fMRI and text datasets.
"""
import os
import sys
import json
import random
from pathlib import Path
from typing import Optional

# Import project utilities
from config import get_config
from utils.logging_config import get_logger, info, error, warning, critical

# Configure logger
logger = get_logger(__name__)

# Constants
ROCSTORIES_DATASET_ID = "rocstories"
DEFAULT_SAMPLE_SIZE = 1000  # Sample size for the subset
OUTPUT_DIR = Path("data/text")
OUTPUT_FILE = OUTPUT_DIR / "rocstories_sample.jsonl"


def download_rocstories_corpus(sample_size: Optional[int] = None) -> bool:
    """
    Download ROCStories corpus via HuggingFace datasets and sample a subset.

    Args:
        sample_size: Number of stories to sample. Defaults to DEFAULT_SAMPLE_SIZE.

    Returns:
        bool: True if successful, False otherwise.

    Raises:
        RuntimeError: If the download fails or data cannot be accessed.
    """
    if sample_size is None:
        sample_size = DEFAULT_SAMPLE_SIZE

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Attempting to download ROCStories corpus (ID: {ROCSTORIES_DATASET_ID})...")

    try:
        from datasets import load_dataset
    except ImportError:
        error("datasets library not found. Please install it via requirements.txt.")
        return False

    try:
        # Load the dataset (streaming to avoid loading full dataset into memory if large)
        # The 'rocstories' dataset on HF typically has 'story' and 'id' or similar fields.
        # We load a subset or stream it to sample.
        dataset = load_dataset(ROCSTORIES_DATASET_ID, split="train", streaming=True)

        # Sample the dataset
        # Note: streaming=True returns an iterator. We can take a slice.
        # To ensure reproducibility, we set a seed from config if available.
        cfg = get_config()
        if cfg and 'random_seed' in cfg:
            random.seed(cfg['random_seed'])
        
        # We need to convert to a list to sample randomly if we want random sampling,
        # or just take the first N if streaming sequentially.
        # Given the constraint of memory and the task to "sample a subset",
        # taking the first N rows from the stream is efficient and valid for a sample.
        # However, to be robust, let's try to collect enough rows.
        
        stories = []
        count = 0
        
        # Iterate and collect
        for item in dataset:
            if count >= sample_size:
                break
            
            # Map fields to expected schema: 'story' (string), 'id' (string/int)
            # HF dataset fields vary. Common ones: 'story', 'story_id', 'id'
            story_text = item.get('story') or item.get('text') or ""
            story_id = item.get('id') or item.get('story_id') or count
            
            if not story_text or not story_text.strip():
                continue
            
            stories.append({
                "story": story_text,
                "id": story_id
            })
            count += 1

        if count == 0:
            error("No valid stories found in the dataset.")
            return False

        # Write to JSONL
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for story_entry in stories:
                f.write(json.dumps(story_entry, ensure_ascii=False) + '\n')

        info(f"Successfully downloaded and sampled {count} stories to {OUTPUT_FILE}")
        return True

    except Exception as e:
        error(f"Failed to download or process ROCStories corpus: {str(e)}")
        raise RuntimeError(f"ROCStories download failed: {str(e)}")


def validate_ingested_data(output_path: Optional[Path] = None) -> bool:
    """
    Validate that the ingested data file exists and conforms to the expected schema.

    Args:
        output_path: Path to the JSONL file. Defaults to OUTPUT_FILE.

    Returns:
        bool: True if valid, False otherwise.
    """
    if output_path is None:
        output_path = OUTPUT_FILE

    if not output_path.exists():
        logger.error(f"Validation failed: File not found at {output_path}")
        return False

    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            line_count = 0
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if 'story' not in record:
                    logger.error(f"Validation failed: Missing 'story' field in {output_path}")
                    return False
                if 'id' not in record:
                    logger.error(f"Validation failed: Missing 'id' field in {output_path}")
                    return False
                if not isinstance(record['story'], str):
                    logger.error(f"Validation failed: 'story' must be a string")
                    return False
                line_count += 1
        
        if line_count == 0:
            logger.error(f"Validation failed: File is empty or contains no valid records")
            return False

        logger.info(f"Validation passed: {line_count} records in {output_path}")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Validation failed: Invalid JSON in {output_path}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {str(e)}")
        return False


def main():
    """
    Main entry point for the data ingestion script.
    """
    info("Starting ROCStories ingestion...")
    
    success = download_rocstories_corpus()
    
    if success:
        if validate_ingested_data():
            info("ROCStories ingestion completed successfully.")
            return 0
        else:
            error("Ingestion produced output, but validation failed.")
            return 1
    else:
        error("Ingestion failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())