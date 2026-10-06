import os
import sys
import csv
import random
import logging
from pathlib import Path

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

# Real data source: nlpconnect/vit-gpt2-image-captioning
DATASET_NAME = "nlpconnect/vit-gpt2-image-captioning"

def fetch_diverse_prompts(num_samples: int = 1000) -> list:
    """
    Fetches diverse text prompts from the real HuggingFace dataset.
    This function strictly adheres to the 'real data only' constraint.
    It will raise an exception if the dataset cannot be fetched.
    """
    logger.info(f"Fetching {num_samples} samples from dataset: {DATASET_NAME}")
    
    try:
        # Load dataset with streaming disabled to ensure local caching and full access
        # The dataset contains 'caption' which is the text prompt
        dataset = load_dataset(DATASET_NAME, split="train", streaming=False)
        
        if len(dataset) == 0:
            raise RuntimeError("The loaded dataset is empty. No real data found.")
        
        # Sample randomly if the dataset is larger than requested
        if len(dataset) > num_samples:
            # Convert to list of dicts for easier sampling
            dataset_list = list(dataset)
            sampled_indices = random.sample(range(len(dataset_list)), num_samples)
            sampled_data = [dataset_list[i] for i in sampled_indices]
        else:
            sampled_data = list(dataset)
        
        # Extract captions
        prompts = []
        for idx, item in enumerate(sampled_data):
            caption = item.get('caption', '').strip()
            if caption:
                prompts.append({
                    'id': f"diverse_{idx}",
                    'caption': caption,
                    'source': DATASET_NAME
                })
        
        logger.info(f"Successfully fetched {len(prompts)} diverse prompts.")
        return prompts

    except Exception as e:
        # Fail loudly as per constraints
        logger.error(f"CRITICAL: Failed to fetch real data from {DATASET_NAME}: {e}")
        raise RuntimeError(f"Real data source unavailable: {e}") from e

def load_coco_captions() -> list:
    """
    Optional helper to load COCO captions if needed for merging.
    For T006d, we focus on the diverse prompts from the HF dataset.
    This function is kept for API compatibility but may not be strictly
    used if T006d is standalone for diverse prompts.
    """
    # If T006d requires merging with T006 output, we would load data/processed/prompts.csv here.
    # For now, we return an empty list as T006d specifically targets diverse_prompts.csv.
    return []

def merge_and_deduplicate(prompts_diverse: list, prompts_coco: list) -> list:
    """
    Merges diverse prompts with COCO captions and deduplicates based on caption text.
    """
    seen_captions = set()
    merged = []

    # Add COCO first (if any)
    for p in prompts_coco:
        if p['caption'] not in seen_captions:
            seen_captions.add(p['caption'])
            merged.append(p)

    # Add diverse prompts
    for p in prompts_diverse:
        if p['caption'] not in seen_captions:
            seen_captions.add(p['caption'])
            merged.append(p)
    
    return merged

def write_merged_csv(prompts: list, filepath: Path):
    """
    Writes the list of prompt dictionaries to a CSV file.
    Expected columns: id, caption, source
    """
    if not prompts:
        raise ValueError("No prompts to write. The dataset fetch must have failed or returned empty.")

    logger.info(f"Writing {len(prompts)} prompts to {filepath}")
    
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'caption', 'source'])
        writer.writeheader()
        writer.writerows(prompts)
    
    logger.info(f"Successfully wrote {filepath}")

def main():
    """
    Main entry point for T006d.
    1. Fetches diverse prompts from HuggingFace.
    2. Writes them to data/processed/diverse_prompts.csv.
    3. Verifies the output file exists and has content.
    """
    try:
        # Fetch real data
        diverse_prompts = fetch_diverse_prompts(num_samples=1000)
        
        # Load COCO prompts if they exist (from T006) to merge, otherwise just use diverse
        coco_prompts = load_coco_captions()
        
        # Merge and deduplicate
        final_prompts = merge_and_deduplicate(diverse_prompts, coco_prompts)
        
        # Write to disk
        write_merged_csv(final_prompts, OUTPUT_FILE)
        
        # Verification
        if not OUTPUT_FILE.exists():
            raise RuntimeError(f"Output file {OUTPUT_FILE} was not created.")
        
        # Check content
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                raise RuntimeError("Output file is empty.")
            if 'id' not in rows[0] or 'caption' not in rows[0] or 'source' not in rows[0]:
                raise RuntimeError("Output file missing required columns: id, caption, source.")
            if not any(r['caption'].strip() for r in rows):
                raise RuntimeError("No non-empty captions found in output.")

        logger.info("T006d completed successfully. Output verified.")
        
    except Exception as e:
        logger.error(f"T006d FAILED: {e}")
        raise

if __name__ == "__main__":
    main()
