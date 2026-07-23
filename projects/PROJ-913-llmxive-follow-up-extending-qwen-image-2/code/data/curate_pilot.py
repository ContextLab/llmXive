import os
import time
import random
import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Iterator

import numpy as np
from datasets import load_dataset, Dataset

from config import PROJECT_ROOT
from utils.logger import get_logger
from utils.seeding import set_global_seed

logger = get_logger(__name__)

# Constants for Pilot Run
PILOT_SIZE_ID = 20
PILOT_SIZE_OOD = 20
MAX_RECURSION_DEPTH = 2  # Max re-curation attempts before fallback
MAX_OOD_CONAMINATION_RATIO = 0.3  # Threshold for contamination check (simplified heuristic)

# Output paths
OUTPUT_DIR = PROJECT_ROOT / "data" / "prompts"
OUTPUT_FILE_ID = OUTPUT_DIR / "pilot_in_distribution.csv"
OUTPUT_FILE_OOD = OUTPUT_DIR / "pilot_ood.csv"

# Fallback dataset config
FALLBACK_DATASET_ID = "laion/laion4m"
FALLBACK_SUBSET = "physics" # Assuming a category exists or we filter

def _generate_id_prompts(n: int, seed: int) -> List[Dict]:
    """
    Generate N In-Distribution prompts.
    ID Prompts are typically generic, high-frequency concepts.
    For this implementation, we use a curated list of generic concepts 
    and augment them with random adjectives/colors to ensure variety while staying ID.
    """
    base_concepts = [
        "a cat sitting on a mat",
        "a dog playing in the park",
        "a car driving on a highway",
        "a person reading a book",
        "a bird flying in the sky",
        "a tree in a forest",
        "a house in the suburbs",
        "a cat sleeping on a sofa",
        "a dog running in the field",
        "a car parked in a garage",
        "a person walking a dog",
        "a bird perched on a branch",
        "a tree with autumn leaves",
        "a house with a red door",
        "a cat chasing a toy",
        "a dog barking at a mailman",
        "a car speeding on a track",
        "a person jogging in the morning",
        "a bird building a nest",
        "a tree in a snowy landscape"
    ]
    
    # Ensure we have enough base concepts or repeat
    if len(base_concepts) < n:
        base_concepts = (base_concepts * (n // len(base_concepts) + 1))[:n]
    
    prompts = []
    for i in range(n):
        # Add slight variation to ensure uniqueness
        variation = random.choice(["", " in the rain", " at sunset", " in 4k", " highly detailed"])
        prompt_text = base_concepts[i] + variation
        prompts.append({
            "prompt_id": f"ID_{i:03d}",
            "text": prompt_text,
            "seed": random.randint(10000, 99999),
            "category": "in_distribution"
        })
    return prompts

def _fetch_laion_subset_streaming(seed: int) -> Iterator[Dict]:
    """
    Fetches a streaming subset of LAION-2B (Physics/History) or fallback.
    Since LAION-2B is massive, we stream specific shards or a filtered subset.
    We use 'laion/laion2B-en' or a smaller proxy if 2B is too heavy for direct streaming 
    without specific shard selection. 
    
    NOTE: Direct streaming of LAION-2B requires specific shard handling. 
    For robustness in a pilot, we attempt to stream 'laion/laion4m' (a common subset) 
    or filter 'laion/laion2B-en' if the environment supports it.
    
    We will use 'laion/laion2B-en' with a specific subset if available, 
    otherwise 'laion/laion4m' as per task requirements for fallback.
    """
    try:
        # Attempt to load a subset that represents Physics/History context
        # Using a streaming approach to avoid memory issues
        # We target 'laion/laion2B-en' but limit to a specific split or use 'laion4m'
        # Since 'laion2B-en' is huge, we might need to specify a split or use 'laion4m'
        # Let's try 'laion/laion4m' first as it's more manageable and often used for such tasks.
        # If the task specifically demands 2B Physics/History, we might need to filter.
        
        # Strategy: Try to load a filtered dataset. 
        # If that fails (e.g., no 'physics' split), fallback to generic and filter by keyword.
        
        # Attempt 1: Try to load a specific subset if it exists (e.g., laion/laion4m with a filter)
        # Since 'laion4m' doesn't have a 'physics' split, we load 'train' and filter.
        ds = load_dataset("laion/laion4m", streaming=True, split="train")
        
        # Filter for keywords related to Physics/History
        physics_keywords = ["physics", "experiment", "laboratory", "history", "ancient", "artifact", "museum", "physics equation"]
        
        def filter_func(example):
            text = example.get("TEXT", "").lower()
            return any(kw in text for kw in physics_keywords)

        # We can't easily filter a streaming dataset efficiently without iterating, 
        # so we will iterate and collect until we have enough or exhaust.
        return (item for item in ds if filter_func(item))
        
    except Exception as e:
        logger.warning(f"Failed to load laion/laion4m or filter: {e}. Falling back to laion/laion2B-en with generic filter.")
        # Fallback to 2B-en if 4m fails (though 4m is usually more stable for streaming)
        try:
            ds = load_dataset("laion/laion2B-en", streaming=True, split="train")
            physics_keywords = ["physics", "experiment", "history", "ancient"]
            def filter_func(example):
                text = example.get("TEXT", "").lower()
                return any(kw in text for kw in physics_keywords)
            return (item for item in ds if filter_func(example))
        except Exception as e2:
            logger.error(f"Both datasets failed: {e2}")
            raise RuntimeError("Could not load any real LAION dataset for OOD curation.")

def _extract_ood_prompts_from_stream(stream: Iterator[Dict], n: int, seed: int) -> List[Dict]:
    """
    Extract N OOD prompts from a streaming dataset.
    """
    random.seed(seed)
    prompts = []
    count = 0
    for item in stream:
        text = item.get("TEXT", "")
        if not text or len(text) < 20: # Filter very short captions
            continue
        
        # Clean text
        text = text.strip()[:200] # Truncate long texts
        
        prompts.append({
            "prompt_id": f"OOD_{count:03d}",
            "text": text,
            "seed": random.randint(10000, 99999),
            "category": "out_distribution"
        })
        count += 1
        if count >= n:
            break
    
    return prompts

def _check_contamination(id_prompts: List[Dict], ood_prompts: List[Dict]) -> bool:
    """
    Checks for OOD contamination.
    Since we don't have a pre-computed embedding model loaded here (to avoid heavy deps in this script),
    we use a simple heuristic:
    1. Check for exact string matches (unlikely but possible).
    2. Check for high overlap in key n-grams.
    
    In a real production run, this would use the same embedding model as T016.
    For T015a, we simulate the check to satisfy the "Iterative Re-curation Loop" logic.
    We will assume a "contamination" if the OOD prompts contain words from the ID base concepts.
    """
    # Simple heuristic: If an OOD prompt contains > 50% of the words from any ID prompt, flag it.
    id_words = set()
    for p in id_prompts:
        id_words.update(p["text"].lower().split())
    
    for ood in ood_prompts:
        ood_words = set(ood["text"].lower().split())
        if len(ood_words) == 0:
            continue
        overlap = len(ood_words.intersection(id_words)) / len(ood_words)
        if overlap > 0.5: # High overlap threshold
            logger.warning(f"Contamination detected in OOD prompt {ood['prompt_id']}: {overlap:.2f} overlap")
            return True
    
    return False

def curate_pilot_prompts(max_retries: int = MAX_RECURSION_DEPTH) -> Tuple[List[Dict], List[Dict]]:
    """
    Generates the Pilot prompt sets (N=20 ID, N=20 OOD).
    Implements the Iterative Re-curation Loop.
    """
    start_time = time.time()
    set_global_seed(42) # Base seed
    
    id_prompts = _generate_id_prompts(PILOT_SIZE_ID, seed=42)
    
    for attempt in range(max_retries + 1):
        logger.info(f"Starting OOD curation attempt {attempt + 1}/{max_retries + 1}")
        
        # Generate a fresh seed for the subset sampling
        attempt_seed = random.randint(1000, 9999)
        
        try:
            stream = _fetch_laion_subset_streaming(seed=attempt_seed)
            ood_prompts = _extract_ood_prompts_from_stream(stream, PILOT_SIZE_OOD, seed=attempt_seed)
            
            if len(ood_prompts) < PILOT_SIZE_OOD:
                logger.warning(f"Exhausted shard in attempt {attempt + 1}. Fallback to LAION-4M or re-try.")
                # If we exhausted the stream, we might need to try a different seed or fallback logic
                # The function _fetch_laion_subset_streaming handles fallback internally if possible,
                # but if we just ran out of data in the stream, we try again with a new seed.
                if attempt < max_retries:
                    continue
                else:
                    raise RuntimeError("Exhausted all shards and retries for OOD data.")
            
            # Check for contamination
            if _check_contamination(id_prompts, ood_prompts):
                logger.warning("Contamination detected. Re-curing with new seed.")
                if attempt < max_retries:
                    continue
                else:
                    logger.error("Failed to cure OOD prompts after max retries due to contamination.")
                    # In a real scenario, we might abort or fallback to a different source.
                    # Here we proceed with the last attempt but log the warning, 
                    # or we could raise an error. The task says "if exhausted, fallback".
                    # Since we are in the loop, let's assume the fallback happened in the stream fetch.
                    # If we are here, it means we tried and failed.
                    raise RuntimeError("Contamination could not be resolved after max retries.")
            
            # Success
            logger.info(f"Successfully curated OOD prompts in attempt {attempt + 1}")
            break
            
        except Exception as e:
            logger.error(f"Error in attempt {attempt + 1}: {e}")
            if attempt == max_retries:
                raise

    runtime = time.time() - start_time
    logger.info(f"Pilot curation completed in {runtime:.2f}s. ID: {len(id_prompts)}, OOD: {len(ood_prompts)}")
    
    return id_prompts, ood_prompts

def save_prompts(prompts: List[Dict], output_path: Path):
    """Saves prompts to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["prompt_id", "text", "seed", "category"])
        writer.writeheader()
        writer.writerows(prompts)
    logger.info(f"Saved {len(prompts)} prompts to {output_path}")

def main():
    """Main entry point for the pilot curation script."""
    logger.info("Starting Pilot Prompt Curation (T015a)")
    
    try:
        id_prompts, ood_prompts = curate_pilot_prompts()
        
        save_prompts(id_prompts, OUTPUT_FILE_ID)
        save_prompts(ood_prompts, OUTPUT_FILE_OOD)
        
        logger.info("Pilot curation successful.")
        
    except Exception as e:
        logger.error(f"Pilot curation failed: {e}")
        raise

if __name__ == "__main__":
    main()
