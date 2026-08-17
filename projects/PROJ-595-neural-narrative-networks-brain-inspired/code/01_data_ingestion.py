import os
import sys
import json
import random
from pathlib import Path
from typing import Optional

from datasets import load_dataset
from config import get_config
from utils.logging_config import get_logger, info, error, warning, critical

logger = get_logger(__name__)

def download_rocstories_corpus(
    output_path: str,
    sample_size: int = 1000,
    seed: int = 42
) -> str:
    """
    Download the ROCStories corpus via HuggingFace datasets and save a representative
    sample to the specified output path in JSONL format.

    This function fetches the real 'rocstories' dataset from HuggingFace,
    shuffles it deterministically, and writes the first `sample_size` stories
    to a JSONL file.

    Args:
        output_path: Path to the output .jsonl file.
        sample_size: Number of stories to sample.
        seed: Random seed for reproducibility.

    Returns:
        The absolute path to the created file.

    Raises:
        RuntimeError: If the dataset cannot be loaded from HuggingFace.
        ValueError: If sample_size is invalid.
    """
    if sample_size <= 0:
        raise ValueError(f"sample_size must be positive, got {sample_size}")

    logger.info(f"Starting ROCStories download and sampling (target: {sample_size} stories)...")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load the real ROCStories dataset from HuggingFace
        # Dataset ID: 'rocstories'
        logger.info("Loading 'rocstories' dataset from HuggingFace...")
        dataset = load_dataset("rocstories", split="train")
        logger.info(f"Dataset loaded successfully. Total stories: {len(dataset)}")
    except Exception as e:
        error(f"Failed to load ROCStories dataset from HuggingFace: {e}")
        raise RuntimeError(f"Could not fetch real ROCStories data: {e}")

    if len(dataset) < sample_size:
        warning(f"Dataset size ({len(dataset)}) is smaller than requested sample ({sample_size}). Using all available stories.")
        sample_size = len(dataset)

    # Deterministic shuffle
    random.seed(seed)
    indices = list(range(len(dataset)))
    random.shuffle(indices)
    sampled_indices = indices[:sample_size]

    logger.info(f"Sampling {sample_size} stories from {len(dataset)} total...")

    # Write to JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        count = 0
        for idx in sampled_indices:
            story = dataset[idx]
            # ROCStories format usually has 'story' or 'sentences' keys.
            # We normalize to a consistent structure if needed, or dump raw.
            # The dataset typically has 'story' (string) or 'sentences' (list of strings).
            # We will store the raw record but ensure it's JSON serializable.
            f.write(json.dumps(story, ensure_ascii=False) + '\n')
            count += 1

        if count != sample_size:
            critical(f"Internal error: Expected to write {sample_size} stories, wrote {count}.")
            raise RuntimeError("Story count mismatch during sampling.")

    logger.info(f"Successfully saved {count} stories to {output_file}")
    return str(output_file)

def main():
    """
    Entry point for the ROCStories download script.
    Reads config, sets paths, and executes the download.
    """
    config = get_config()
    seed = config.get('random_seed', 42)
    sample_size = 1000  # Representative subset size as per task description

    # Output path as defined in tasks.md
    output_path = "data/text/rocstories_sample.jsonl"

    try:
        result_path = download_rocstories_corpus(
            output_path=output_path,
            sample_size=sample_size,
            seed=seed
        )
        info(f"Task T019 completed: ROCStories corpus saved to {result_path}")
        return 0
    except Exception as e:
        error(f"Task T019 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
