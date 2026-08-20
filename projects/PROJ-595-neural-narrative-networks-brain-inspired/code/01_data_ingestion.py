import os
import sys
import json
import random
from pathlib import Path
from typing import Optional

# Import config and logging utilities from the project
from config import get_config
from utils.logging_config import get_logger, info, error, warning, critical

logger = get_logger(__name__)

def download_rocstories_corpus(output_dir: Optional[str] = None, sample_size: int = 1000, seed: int = 42) -> str:
    """
    Downloads the ROCStories corpus from HuggingFace datasets and saves a sampled subset.
    
    Args:
        output_dir: Directory to save the output file. Defaults to 'data/text/'.
        sample_size: Number of stories to sample.
        seed: Random seed for reproducibility.
        
    Returns:
        Path to the saved JSONL file.
        
    Raises:
        RuntimeError: If the download fails or the dataset is unavailable.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise RuntimeError("The 'datasets' package is required. Install it via 'pip install datasets'.")

    if output_dir is None:
        output_dir = "data/text"
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    final_file = output_path / "rocstories_sample.jsonl"
    
    logger.info(f"Attempting to download ROCStories corpus from HuggingFace...")
    
    # The dataset identifier for ROCStories on HuggingFace
    dataset_id = "rocstories"
    
    try:
        # Load the dataset with streaming to avoid downloading the full corpus if not needed
        # We specifically request the 'train' split which usually contains the bulk of the data
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        # Set random seed for sampling
        random.seed(seed)
        
        # Sample the dataset
        # Since streaming doesn't support direct random sampling of the whole set without buffering,
        # we will collect the first N items if the dataset is small enough, or sample on the fly.
        # Given the constraint of ~7GB RAM, we'll stream and sample efficiently.
        
        sampled_stories = []
        count = 0
        
        # We need a representative sample. For ROCStories, the dataset is manageable in memory
        # but we'll use a reservoir sampling approach or simple limit if we just want N items.
        # The task asks for a "representative subset". Taking the first N is a common strategy
        # if the dataset is ordered, but random sampling is better.
        # To be safe and robust, we will try to load the full list of IDs if possible or stream.
        # However, standard practice for a "sample" in this context is often just the first N
        # or a random N if we can index. Let's try to load the dataset normally first.
        
        # Fallback to non-streaming if we need to sample randomly from the whole set without
        # knowing the total count, but for ROCStories, the total size is known (~98k stories).
        # We will load the full dataset into memory as it fits in RAM (it's text).
        ds_full = load_dataset(dataset_id, split="train")
        
        total_size = len(ds_full)
        if sample_size > total_size:
            logger.warning(f"Requested sample size {sample_size} exceeds dataset size {total_size}. Using full dataset.")
            sample_size = total_size
        
        indices = random.sample(range(total_size), sample_size)
        
        for i in indices:
            item = ds_full[i]
            # ROCStories structure: usually has 'story' (list of sentences) or 'text'
            # We need to normalize to a consistent JSON format.
            # Standard ROCStories often has 'story' as a list of 5 sentences.
            if 'story' in item:
                story_text = " ".join(item['story'])
            elif 'text' in item:
                story_text = item['text']
            else:
                # Fallback for unexpected schema
                story_text = str(item)
            
            sampled_stories.append({"story": story_text, "source": "rocstories", "id": i})
        
        # Write to JSONL
        with open(final_file, 'w', encoding='utf-8') as f:
            for story in sampled_stories:
                f.write(json.dumps(story, ensure_ascii=False) + '\n')
                
        logger.info(f"Successfully downloaded and sampled {len(sampled_stories)} stories to {final_file}")
        return str(final_file)
        
    except Exception as e:
        logger.error(f"Failed to download or process ROCStories dataset: {str(e)}")
        raise RuntimeError(f"ROCStories download failed: {str(e)}")

def validate_ingested_data(file_path: str) -> bool:
    """
    Validates that the downloaded JSONL file exists and is not empty.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        True if valid, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Validation failed: File {file_path} does not exist.")
        return False
    
    if path.stat().st_size == 0:
        logger.error(f"Validation failed: File {file_path} is empty.")
        return False
    
    # Basic check: can we read one line?
    try:
        with open(path, 'r', encoding='utf-8') as f:
            line = f.readline()
            if line:
                json.loads(line)
            else:
                logger.error("Validation failed: File appears to be empty or malformed.")
                return False
    except json.JSONDecodeError as e:
        logger.error(f"Validation failed: Invalid JSON in {file_path}: {e}")
        return False
    
    logger.info(f"Validation passed for {file_path}")
    return True

def main():
    """
    Main entry point for the data ingestion script.
    """
    config = get_config()
    sample_size = 1000  # Default sample size as per task requirement for a "representative subset"
    
    logger.info("Starting ROCStories corpus ingestion (Task T019)...")
    
    try:
        output_file = download_rocstories_corpus(sample_size=sample_size, seed=config.get('random_seed', 42))
        
        if validate_ingested_data(output_file):
            logger.info("Task T019 completed successfully.")
            return 0
        else:
            logger.error("Task T019 failed: Validation of ingested data failed.")
            return 1
            
    except RuntimeError as e:
        logger.error(f"Task T019 failed with error: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error during T019: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
