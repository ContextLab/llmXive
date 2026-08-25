"""
Data Ingestion Module for Neural Narrative Networks.
Handles downloading and preprocessing of text corpora (ROCStories) and fMRI data.
"""
import os
import sys
import json
import random
from pathlib import Path
from typing import Optional

# Import config and logging utilities
try:
    from config import get_config
    from utils.logging_config import get_logger, info, error, warning, critical
except ImportError:
    # Fallback for direct execution or different environment setup
    # In a real run, these should be available via PYTHONPATH
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def get_config():
        return {"random_seed": 42, "cpu_only": True, "max_ram_gb": 7}
    
    def info(msg): logger.info(msg)
    def error(msg): logger.error(msg)
    def warning(msg): logger.warning(msg)
    def critical(msg): logger.critical(msg)

def download_rocstories_corpus(output_dir: str, sample_size: int = 1000, seed: int = 42) -> str:
    """
    Downloads the ROCStories corpus from HuggingFace datasets and saves a sampled subset.
    
    Args:
        output_dir: Directory to save the output file.
        sample_size: Number of stories to sample.
        seed: Random seed for reproducibility.
        
    Returns:
        Path to the saved JSONL file.
        
    Raises:
        RuntimeError: If the download fails or data cannot be retrieved.
    """
    config = get_config()
    random.seed(seed)
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / "rocstories_sample.jsonl"
    
    info(f"Attempting to download ROCStories corpus from HuggingFace...")
    
    try:
        # Import datasets here to avoid hard dependency if not needed
        from datasets import load_dataset
        
        # Load the ROCStories dataset (rochestories is the standard name)
        # We load only the 'train' split which contains the stories
        dataset = load_dataset("rocstories", split="train", trust_remote_code=True)
        
        if len(dataset) == 0:
            raise RuntimeError("Downloaded dataset is empty.")
        
        info(f"Successfully loaded {len(dataset)} stories from ROCStories.")
        
        # Sample the data
        if sample_size >= len(dataset):
            sampled_data = dataset
            info(f"Sample size ({sample_size}) >= dataset size. Using full dataset.")
        else:
            # Use dataset's select or random sampling
            # To ensure reproducibility with seed, we can shuffle indices
            indices = list(range(len(dataset)))
            random.shuffle(indices)
            selected_indices = indices[:sample_size]
            sampled_data = dataset.select(selected_indices)
            info(f"Sampled {sample_size} stories from {len(dataset)} total.")
        
        # Write to JSONL
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in sampled_data:
                # Ensure we write the story text. ROCStories usually has 'story' or 'sentences'
                # The dataset structure typically has 'story' as a single string or 'sentences' as list
                # We normalize to a single 'text' field for downstream processing
                story_text = item.get('story', None)
                if not story_text and 'sentences' in item:
                    story_text = ' '.join(item['sentences'])
                
                if story_text:
                    record = {
                        "text": story_text.strip(),
                        "source": "rocstories",
                        "id": item.get('story_id', 'unknown')
                    }
                    f.write(json.dumps(record) + '\n')
                else:
                    warning(f"Skipping item with no text content: {item.get('story_id', 'unknown')}")
        
        info(f"Successfully saved sampled ROCStories to {output_file}")
        return str(output_file)
        
    except ImportError:
        error("The 'datasets' library is required but not installed. Please install it via 'pip install datasets'.")
        raise RuntimeError("Missing dependency: 'datasets' library not found.")
    except Exception as e:
        error(f"Failed to download or process ROCStories corpus: {str(e)}")
        raise RuntimeError(f"Data ingestion failed: {str(e)}")


def validate_ingested_data(file_path: str) -> bool:
    """
    Validates that the ingested text file exists and is not empty.
    
    Args:
        file_path: Path to the file to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        error(f"Validation failed: File does not exist: {file_path}")
        return False
    
    if path.stat().st_size == 0:
        error(f"Validation failed: File is empty: {file_path}")
        return False
    
    # Basic check for JSONL format
    try:
        with open(path, 'r', encoding='utf-8') as f:
            line_count = 0
            for line in f:
                if line.strip():
                    json.loads(line)
                    line_count += 1
        if line_count == 0:
            error(f"Validation failed: No valid JSON lines found in {file_path}")
            return False
        info(f"Validation passed: {line_count} valid records in {file_path}")
        return True
    except json.JSONDecodeError as e:
        error(f"Validation failed: Invalid JSON in {file_path}: {e}")
        return False


def main():
    """
    Main entry point for data ingestion.
    """
    config = get_config()
    seed = config.get('random_seed', 42)
    
    # Define paths
    data_root = Path("data")
    text_dir = data_root / "text"
    
    # Ensure directories exist (T005 equivalent)
    text_dir.mkdir(parents=True, exist_ok=True)
    
    # Download and sample ROCStories
    output_file = download_rocstories_corpus(
        output_dir=str(text_dir),
        sample_size=1000,
        seed=seed
    )
    
    # Validate
    if validate_ingested_data(output_file):
        info("Data ingestion pipeline completed successfully.")
        return 0
    else:
        error("Data ingestion pipeline failed validation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())