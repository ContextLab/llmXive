"""
Data ingestion module for downloading and preparing external datasets.
Handles ROCStories corpus via HuggingFace datasets.
"""
import os
import sys
from pathlib import Path
from typing import Optional

from config import get_config
from utils.logging_config import get_logger, info, error, warning

# Import datasets dynamically to avoid hard dependency if not installed,
# but the task requires it to be present.
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. Please install it via: "
        "pip install datasets"
    )

def download_rocstories_corpus(
    output_path: str,
    sample_size: int = 1000,
    seed: int = 42
) -> None:
    """
    Downloads the ROCStories corpus from HuggingFace and saves a representative
    subset to a JSONL file.

    Args:
        output_path: Full path to the output .jsonl file.
        sample_size: Number of stories to sample.
        seed: Random seed for reproducibility.
    """
    logger = get_logger(__name__)
    info(f"Starting ROCStories download to {output_path}")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load the 'rocstories' dataset from HuggingFace
        # The dataset name is 'rocstories' and it contains 'train', 'validation', 'test' splits.
        # We use the 'train' split for sampling.
        logger.info("Loading ROCStories dataset from HuggingFace...")
        dataset = load_dataset("rocstories", split="train", streaming=True)

        # Sample the dataset
        # Since we are streaming, we iterate and take the first N items.
        # This avoids loading the whole dataset into memory.
        logger.info(f"Sampling {sample_size} stories with seed {seed}...")
        
        sampled_stories = []
        count = 0
        
        # Use a simple counter for sampling to ensure determinism with seed
        # Note: Streaming datasets from HF don't always support .shuffle() directly
        # in a way that guarantees order across runs without caching.
        # We will iterate and collect.
        import random
        random.seed(seed)
        
        # To get a truly random sample without loading all, we could use reservoir sampling,
        # but for a "representative subset" of a fixed size from a known stream,
        # taking the first N after a shuffle (if we can shuffle) or just first N is common.
        # However, HF streaming allows .shuffle() which buffers.
        # Let's use a buffer-based shuffle for a small sample size relative to dataset.
        # Or simpler: just take the first N if the dataset is already randomized enough,
        # or implement a simple reservoir if we wanted random from infinite.
        # Given the constraint "representative subset", taking the first N after a shuffle
        # of a small buffer is acceptable, or just the first N if the dataset is large.
        # Let's use reservoir sampling for true randomness without full load.
        
        reservoir = []
        for idx, item in enumerate(dataset):
            if idx < sample_size:
                reservoir.append(item)
            else:
                s = random.randint(0, idx)
                if s < sample_size:
                    reservoir[s] = item
        
        sampled_stories = reservoir
        logger.info(f"Successfully sampled {len(sampled_stories)} stories.")

        # Write to JSONL
        logger.info(f"Writing to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            for story in sampled_stories:
                # Ensure the story is a dict and convert to JSON string
                # The dataset usually returns dicts with keys like 'story', 'ending1', etc.
                f.write(json.dumps(story) + '\n')

        info(f"ROCStories corpus saved to {output_path}")

    except Exception as e:
        error(f"Failed to download or process ROCStories: {e}")
        raise

def main() -> None:
    """Main entry point for the data ingestion script."""
    config = get_config()
    output_path = str(Path(config['data_dir']) / "text" / "rocstories_sample.jsonl")
    
    # Ensure the text directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    download_rocstories_corpus(
        output_path=output_path,
        sample_size=1000,
        seed=config.get('random_seed', 42)
    )

if __name__ == "__main__":
    main()
