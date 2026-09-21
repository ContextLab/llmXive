"""
download_diverse_prompts.py

Fetches a diverse set of text prompts from verified public repositories on HuggingFace Hub
and merges them with the existing MS-COCO captions.

CRITICAL: This script uses REAL data sources only. No synthetic fallbacks are permitted.
If the real source cannot be fetched, the script will raise an exception and fail loudly.

The output file is written to: data/processed/prompts_diverse.csv
This file is intended to be merged with MS-COCO captions for the DiT generation pass in T017.
"""
import os
import sys
import csv
import random
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import Config
from datasets import load_dataset

# Verified real data source: "HuggingFaceFW/fineweb-edu" or similar text-heavy datasets
# However, for specific "diverse prompts" suitable for image generation, a curated dataset
# or a specific subset of a large text dataset is better.
# We will use "lambada_openai" or "c4" subset, but specifically,
# the task asks for "diverse text prompts".
# A verified source for diverse captions/prompts often used in diffusion research is
# "laion/laion2B-en" (too big) or specific subsets.
# To ensure reliability and diversity within a reasonable fetch time, we use
# "HuggingFaceH4/ultrachat_200k" (user prompts) or "stas/openwebtext-10k" for diversity.
# Given the context of "prompts" for diffusion, we will use a subset of "HuggingFaceH4/ultrachat_200k"
# which contains diverse user instructions, or "lambada_openai" for natural language diversity.
#
# DECISION: Use "HuggingFaceH4/ultrachat_200k" (split: train) -> 'prompt' column.
# This provides diverse, human-written prompts.
# If this fails, we fall back to "stas/openwebtext-10k" (split: train) -> 'text'.
# We will try the primary source first and fail loudly if it is unreachable.

DATASET_SOURCE_PRIMARY = "HuggingFaceH4/ultrachat_200k"
DATASET_SOURCE_PRIMARY_COLUMN = "prompt" # The user prompt
DATASET_SOURCE_PRIMARY_SPLIT = "train"

DATASET_SOURCE_FALLBACK = "stas/openwebtext-10k"
DATASET_SOURCE_FALLBACK_COLUMN = "text"
DATASET_SOURCE_FALLBACK_SPLIT = "train"

# We need a specific number of diverse prompts. The task doesn't specify N,
# but T017 needs a "curated set". We will fetch a reasonable sample (e.g., 5000)
# to ensure diversity without overwhelming the runner if not needed.
# However, to be safe on memory, we will stream and take a sample.
SAMPLE_SIZE = 5000
SEED = 42

def fetch_diverse_prompts(
    source: str,
    column: str,
    split: str,
    sample_size: int,
    seed: int
) -> List[str]:
    """
    Fetches prompts from a HuggingFace dataset.
    Raises an exception if the dataset cannot be loaded or if no data is found.
    """
    print(f"Fetching diverse prompts from: {source} (column: {column}, split: {split})")
    
    try:
        # Use streaming to avoid downloading the whole dataset if it's large
        # We need to collect a sample, so we iterate.
        dataset = load_dataset(
            source,
            split=split,
            streaming=True,
            trust_remote_code=True
        )
    except Exception as e:
        raise RuntimeError(f"CRITICAL: Failed to load dataset '{source}' from HuggingFace Hub. "
                           f"No synthetic fallback allowed. Error: {e}")

    prompts = []
    seen = set()
    
    # Random sampling logic
    rng = random.Random(seed)
    
    iterator = iter(dataset)
    count = 0
    
    for item in iterator:
        if len(prompts) >= sample_size:
            break
        
        # Extract text
        text = item.get(column)
        if not text or not isinstance(text, str):
            continue
        
        text = text.strip()
        if not text:
            continue
        
        # Deduplicate
        if text in seen:
            continue
        
        # Simple cleaning to ensure it's a valid prompt (no newlines that break CSV easily, though CSV handles them)
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Add to sample with reservoir or simple random selection if we wanted random from stream
        # Here we just take the first N unique ones after shuffling isn't possible on stream easily without reservoir.
        # For a "diverse" set, taking the first 5000 unique from a large stream is acceptable.
        # To make it more robust, we could do reservoir sampling, but simple unique collection is fine for now.
        
        prompts.append(text)
        seen.add(text)
        count += 1

    if len(prompts) == 0:
        raise RuntimeError(f"CRITICAL: No valid prompts found in '{source}'. "
                           f"Dataset might be empty or column '{column}' missing. "
                           f"No synthetic fallback allowed.")
    
    print(f"Successfully fetched {len(prompts)} unique diverse prompts.")
    return prompts

def load_coco_captions(config: Config) -> List[Dict[str, Any]]:
    """
    Loads existing MS-COCO captions from the preprocessed file generated by T006.
    Assumes the file exists at config.OUTPUT_PROMPTS_PATH.
    """
    coco_path = config.OUTPUT_PROMPTS_PATH
    if not coco_path.exists():
        raise FileNotFoundError(f"CRITICAL: MS-COCO prompts file not found at {coco_path}. "
                                f"Run T006 (preprocess.py) first.")
    
    captions = []
    with open(coco_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure we have the 'prompt' or 'caption' key
            key = 'prompt' if 'prompt' in row else 'caption'
            if key in row:
                captions.append({
                    "source": "ms_coco",
                    "text": row[key]
                })
    return captions

def merge_and_deduplicate(existing_captions: List[Dict[str, Any]], new_prompts: List[str]) -> List[Dict[str, Any]]:
    """
    Merges existing captions with new diverse prompts, removing duplicates.
    """
    seen_texts = {c["text"].strip().lower() for c in existing_captions}
    merged = list(existing_captions)
    
    for p in new_prompts:
        p_clean = p.strip().lower()
        if p_clean not in seen_texts:
            merged.append({
                "source": "diverse_external",
                "text": p
            })
            seen_texts.add(p_clean)
    
    return merged

def write_merged_csv(merged_data: List[Dict[str, Any]], output_path: Path):
    """
    Writes the merged dataset to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['source', 'prompt']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in merged_data:
            writer.writerow({
                'source': item['source'],
                'prompt': item['text']
            })
    
    print(f"Wrote {len(merged_data)} prompts to {output_path}")

def main():
    config = Config()
    
    # Step 1: Load existing MS-COCO captions
    print("Loading existing MS-COCO captions...")
    coco_captions = load_coco_captions(config)
    print(f"Loaded {len(coco_captions)} MS-COCO captions.")
    
    # Step 2: Fetch diverse prompts from verified source
    diverse_prompts = []
    
    # Try primary source
    try:
        diverse_prompts = fetch_diverse_prompts(
            DATASET_SOURCE_PRIMARY,
            DATASET_SOURCE_PRIMARY_COLUMN,
            DATASET_SOURCE_PRIMARY_SPLIT,
            SAMPLE_SIZE,
            SEED
        )
    except Exception as e:
        print(f"Warning: Primary source failed: {e}. Attempting fallback...")
        try:
            diverse_prompts = fetch_diverse_prompts(
                DATASET_SOURCE_FALLBACK,
                DATASET_SOURCE_FALLBACK_COLUMN,
                DATASET_SOURCE_FALLBACK_SPLIT,
                SAMPLE_SIZE,
                SEED
            )
        except Exception as e2:
            # Fail loudly if both fail
            raise RuntimeError(f"CRITICAL: All data sources failed. "
                               f"Primary: {DATASET_SOURCE_PRIMARY}, Fallback: {DATASET_SOURCE_FALLBACK}. "
                               f"Cannot proceed without real data. Error: {e2}")
    
    # Step 3: Merge and deduplicate
    print("Merging and deduplicating...")
    merged_data = merge_and_deduplicate(coco_captions, diverse_prompts)
    
    # Step 4: Write output
    output_path = config.OUTPUT_PROMPTS_PATH.parent / "prompts_diverse.csv"
    write_merged_csv(merged_data, output_path)
    
    print("Task T006a completed successfully.")

if __name__ == "__main__":
    main()
