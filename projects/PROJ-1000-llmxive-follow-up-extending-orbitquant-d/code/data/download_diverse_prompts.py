"""
Fetch a diverse set of text prompts from a publicly accessible HuggingFace
dataset and write them to ``data/processed/diverse_prompts.csv``.

The script raises ``RuntimeError`` on any failure – no synthetic fallback.
"""
import os
import sys
import csv
import random
import logging
from pathlib import Path
from typing import List, Dict

from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure output directory exists
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "diverse_prompts.csv"

# Real data source: COCO captions (train split) – provides a large, diverse set of captions
DATASET_NAME = "nlpconnect/coco_captions"
SPLIT = "train"

def fetch_diverse_prompts(num_samples: int = 1000) -> List[Dict[str, str]]:
    """
    Fetches diverse text prompts from the COCO training split.
    Raises an exception if the dataset cannot be fetched.
    """
    logger.info(f"Fetching {num_samples} samples from dataset: {DATASET_NAME} ({SPLIT})")
    try:
        # Load the full dataset (non‑streaming) to allow random sampling
        dataset = load_dataset(DATASET_NAME, split=SPLIT, streaming=False)
    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_NAME}: {e}")
        raise RuntimeError(f"Real data source unavailable: {e}") from e

    if len(dataset) == 0:
        raise RuntimeError("The loaded dataset is empty. No real data found.")

    # Randomly sample if more records than needed
    if len(dataset) > num_samples:
        dataset_list = list(dataset)
        sampled_indices = random.sample(range(len(dataset_list)), num_samples)
        sampled_data = [dataset_list[i] for i in sampled_indices]
    else:
        sampled_data = list(dataset)

    prompts = []
    for idx, item in enumerate(sampled_data):
        caption = item.get('caption')
        if isinstance(caption, str):
            caption = caption.strip()
        if caption:
            prompts.append({
                'id': f"diverse_{idx}",
                'caption': caption,
                'source': f"{DATASET_NAME}:{SPLIT}"
            })

    logger.info(f"Successfully fetched {len(prompts)} diverse prompts.")
    return prompts

def write_prompts_to_csv(prompts: List[Dict[str, str]], filepath: Path) -> None:
    """
    Writes prompt dictionaries to ``filepath`` as CSV with columns
    ``id, caption, source``.
    """
    if not prompts:
        raise RuntimeError("No prompts to write – dataset fetch returned empty list.")
    logger.info(f"Writing {len(prompts)} prompts to {filepath}")
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'caption', 'source'])
        writer.writeheader()
        writer.writerows(prompts)
    logger.info(f"Wrote prompts to {filepath}")

def main() -> None:
    """
    Main entry point:
    1. Fetch diverse prompts.
    2. Write them to ``data/processed/diverse_prompts.csv``.
    """
    try:
        prompts = fetch_diverse_prompts(num_samples=1000)
        write_prompts_to_csv(prompts, OUTPUT_FILE)

        # Verification
        if not OUTPUT_FILE.is_file():
            raise RuntimeError(f"Output file {OUTPUT_FILE} was not created.")
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                raise RuntimeError("Output file is empty.")
            required = {'id', 'caption', 'source'}
            if not required.issubset(set(rows[0].keys())):
                raise RuntimeError(f"Missing required columns in {OUTPUT_FILE}")
            if not any(r['caption'].strip() for r in rows):
                raise RuntimeError("All captions are empty.")
        logger.info("Diverse prompts download completed successfully.")
    except Exception as e:
        logger.error(f"Diverse prompts download failed: {e}")
        raise

if __name__ == "__main__":
    main()
