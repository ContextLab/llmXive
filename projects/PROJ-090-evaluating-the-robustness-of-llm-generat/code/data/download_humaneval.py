"""
HumanEval Data Downloader
Downloads the HumanEval dataset from Hugging Face and saves it to data/raw/.

This script implements T012: Implement HumanEval download script.
It uses the real 'openai_humaneval' dataset from Hugging Face and fails loudly
if the download fails, without any synthetic fallback.
"""

import os
import sys
import json
from pathlib import Path
from datasets import load_dataset
from config import ensure_directories
from utils.logging import get_perturbation_logger

logger = get_perturbation_logger()
DATA_DIR = Path("data/raw")
OUTPUT_FILE = DATA_DIR / "humaneval.json"

def download_humaneval() -> Path:
    """
    Downloads HumanEval dataset from Hugging Face.
    Returns the path to the saved JSON file.
    
    Raises:
        RuntimeError: If the real dataset cannot be downloaded.
    """
    ensure_directories()
    
    if OUTPUT_FILE.exists():
        logger.info(f"HumanEval data already exists at {OUTPUT_FILE}")
        logger.info("Skipping download. To re-download, delete the existing file.")
        return OUTPUT_FILE

    logger.info("Downloading HumanEval dataset from 'openai_humaneval'...")
    try:
        # Load from Hugging Face datasets
        # The dataset name is 'openai_humaneval' as per standard HF repository
        # We use streaming=False to load the whole dataset into memory for processing
        # The dataset is small (~164 samples), so this is safe.
        dataset = load_dataset("openai_humaneval", split="test")
        
        logger.info(f"Loaded {len(dataset)} samples from dataset.")
        
        # Convert to list of dicts and save
        data_list = []
        for item in dataset:
            data_list.append({
                "task_id": item["task_id"],
                "prompt": item["prompt"],
                "canonical_solution": item["canonical_solution"],
                "test": item["test"],
                "entry_point": item["entry_point"]
            })

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved HumanEval data to {OUTPUT_FILE}")
        logger.info(f"File size: {OUTPUT_FILE.stat().st_size} bytes")
        return OUTPUT_FILE

    except Exception as e:
        logger.error(f"Failed to download HumanEval: {e}")
        # Fail loudly as per constraints - no synthetic fallback
        raise RuntimeError(f"Could not load real HumanEval data from 'openai_humaneval': {e}")

def main():
    """CLI entry point."""
    try:
        path = download_humaneval()
        if path:
            print(f"Data ready at: {path}")
            return 0
        return 1
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())