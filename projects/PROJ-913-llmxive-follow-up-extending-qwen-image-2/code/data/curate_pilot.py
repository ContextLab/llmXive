"""
Pilot Prompt Curation Module (T015a)

Generates Pilot prompt sets (N=20 ID, N=20 OOD) from real LAION-2B shards.
Implements strict abort logic and re-sampling mechanisms as per spec.
"""
import os
import time
import random
import csv
import hashlib
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from datasets import load_dataset
import numpy as np
from sentence_transformers import SentenceTransformer

# Project Imports
from config import PROJECT_ROOT
from utils.logger import get_logger
from utils.seeding import set_global_seed

logger = get_logger(__name__)

# Constants
PILOT_SIZE = 20
MAX_RECURSION_DEPTH = 2  # Max re-curation attempts before abort
SIMILARITY_THRESHOLD = 0.3
# Primary and Alternative shards for LAION-2B (Physics/History focus)
# We use 'laion/laion2B-en' which is the standard filtered subset.
# We will filter for specific concepts in the prompt generation logic.
SHARDS = [
    "laion/laion2B-en", 
    # Alternative shards if primary is exhausted or rate-limited
    "laion/laion-coco", 
    "laion/laion-high-resolution"
]
CONCEPTS = {
    "physics": ["quantum", "relativity", "thermodynamics", "electromagnetism", "particle physics", "astrophysics", "nucleus", "photon", "entropy", "gravity"],
    "history": ["ancient rome", "renaissance", "industrial revolution", "world war", "medieval", "victorian era", "imperial china", "egyptian pharaoh", "greek philosophy", "ottoman empire"]
}

def get_id_centroid_embeddings(embedding_model, prompts: List[str]) -> np.ndarray:
    """
    Computes the centroid of embeddings for a list of ID prompts.
    """
    logger.info(f"Computing centroid for {len(prompts)} ID prompts...")
    embeddings = embedding_model.encode(prompts, show_progress_bar=True, convert_to_numpy=True)
    return np.mean(embeddings, axis=0)

def check_contamination(
    ood_prompts: List[str], 
    id_centroid: np.ndarray, 
    embedding_model: SentenceTransformer
) -> bool:
    """
    Checks if OOD prompts have contamination (similarity > threshold) to ID centroid.
    Returns True if contamination is detected.
    """
    logger.info("Checking for OOD contamination...")
    ood_embeddings = embedding_model.encode(ood_prompts, show_progress_bar=True, convert_to_numpy=True)
    
    for i, emb in enumerate(ood_embeddings):
        # Cosine similarity
        similarity = np.dot(ood_embeddings[i], id_centroid) / (np.linalg.norm(ood_embeddings[i]) * np.linalg.norm(id_centroid))
        if similarity > SIMILARITY_THRESHOLD:
            logger.warning(f"Contamination detected: OOD prompt '{ood_prompts[i]}' has similarity {similarity:.4f} > {SIMILARITY_THRESHOLD}")
            return True
    return False

def fetch_prompts_from_shard(shard_name: str, concepts: List[str], count: int, seed: int) -> List[str]:
    """
    Fetches prompts from a specific LAION shard filtered by concepts.
    """
    logger.info(f"Fetching {count} prompts from shard '{shard_name}' with concepts: {concepts}")
    try:
        # Load dataset in streaming mode to handle large sizes
        ds = load_dataset(shard_name, streaming=True, split="train")
        
        # Filter logic: We need prompts that match concepts for ID, 
        # or are distinct for OOD. Since LAION captions are free-text,
        # we simulate "Physics/History" ID by filtering for those keywords,
        # and OOD by filtering for "Nature/Art" or other distinct categories.
        
        # Note: In a real strict pipeline, we would have a pre-curated list of IDs.
        # Here we generate them dynamically from the stream.
        
        id_prompts = []
        ood_prompts = []
        
        # Define OOD concepts (Nature/Abstract) to contrast with Physics/History
        ood_concepts = ["sunset", "ocean", "forest", "mountain", "flower", "abstract art", "portrait", "landscape", "cloud", "river"]
        
        # We iterate until we have enough samples
        # Using a timeout or max iterations to prevent hanging on bad shards
        max_iterations = count * 100 
        current_iter = 0
        
        for item in ds:
            if current_iter > max_iterations:
                logger.warning(f"Shard '{shard_name}' exhausted before reaching target count.")
                break
            
            caption = item.get("caption", "")
            if not caption:
                continue
            
            caption_lower = caption.lower()
            
            # Check ID
            if len(id_prompts) < count:
                if any(kw in caption_lower for kw in concepts):
                    id_prompts.append(caption)
                    continue
            
            # Check OOD (using a different set of concepts for variety)
            if len(ood_prompts) < count:
                if any(kw in caption_lower for kw in ood_concepts):
                    # Ensure it's not accidentally an ID concept
                    if not any(kw in caption_lower for kw in concepts):
                        ood_prompts.append(caption)
            
            current_iter += 1
            
            if len(id_prompts) >= count and len(ood_prompts) >= count:
                break

        return id_prompts[:count], ood_prompts[:count]

    except Exception as e:
        logger.error(f"Failed to fetch from shard '{shard_name}': {e}")
        raise e

def curate_pilot_prompts(seed: Optional[int] = None, recursion_depth: int = 0) -> Tuple[List[str], List[str]]:
    """
    Main function to curate Pilot prompts.
    
    Logic:
    1. Set seed.
    2. Load embedding model.
    3. Fetch ID and OOD prompts from LAION shards.
    4. Check for contamination.
    5. If contamination or failure, retry with new seed (up to MAX_RECURSION_DEPTH).
    6. If still failing, ABORT.
    """
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    set_global_seed(seed)
    logger.info(f"Starting curate_pilot_prompts with seed {seed}, recursion depth {recursion_depth}")
    start_time = time.time()
    
    # Load embedding model (CLIP is standard, but we use a lightweight one for speed if needed)
    # Using 'all-MiniLM-L6-v2' for fast embedding
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Select concepts
    all_id_concepts = CONCEPTS["physics"] + CONCEPTS["history"]
    
    # Try to fetch from shards
    id_prompts = []
    ood_prompts = []
    success = False
    
    for shard in SHARDS:
        try:
            id_prompts, ood_prompts = fetch_prompts_from_shard(shard, all_id_concepts, PILOT_SIZE, seed)
            if len(id_prompts) == PILOT_SIZE and len(ood_prompts) == PILOT_SIZE:
                success = True
                break
        except Exception as e:
            logger.error(f"Shard {shard} failed: {e}")
            continue
    
    if not success:
        logger.critical("All shards exhausted or failed to yield sufficient prompts.")
        if recursion_depth < MAX_RECURSION_DEPTH:
            logger.info(f"Retrying with new seed (depth {recursion_depth + 1})...")
            new_seed = random.randint(0, 2**32 - 1)
            return curate_pilot_prompts(seed=new_seed, recursion_depth=recursion_depth + 1)
        else:
            logger.critical("Max recursion depth reached. ABORTING.")
            sys.exit(1)
    
    # Compute ID Centroid
    id_centroid = get_id_centroid_embeddings(embedding_model, id_prompts)
    
    # Check Contamination
    if check_contamination(ood_prompts, id_centroid, embedding_model):
        logger.critical("OOD Contamination detected.")
        if recursion_depth < MAX_RECURSION_DEPTH:
            logger.info(f"Retrying with new seed to avoid contamination (depth {recursion_depth + 1})...")
            new_seed = random.randint(0, 2**32 - 1)
            return curate_pilot_prompts(seed=new_seed, recursion_depth=recursion_depth + 1)
        else:
            logger.critical("Max recursion depth reached. ABORTING due to persistent contamination.")
            sys.exit(1)
    
    elapsed = time.time() - start_time
    logger.info(f"Pilot curation successful in {elapsed:.2f}s. ID: {len(id_prompts)}, OOD: {len(ood_prompts)}")
    
    return id_prompts, ood_prompts

def save_prompts(id_prompts: List[str], ood_prompts: List[str], output_dir: Path):
    """
    Saves the curated prompts to CSV files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    id_path = output_dir / "pilot_in_distribution.csv"
    ood_path = output_dir / "pilot_ood.csv"
    
    with open(id_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['prompt_id', 'prompt_text', 'category'])
        for i, prompt in enumerate(id_prompts):
            writer.writerow([f"id_{i:03d}", prompt, "physics_history"])
    
    with open(ood_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['prompt_id', 'prompt_text', 'category'])
        for i, prompt in enumerate(ood_prompts):
            writer.writerow([f"ood_{i:03d}", prompt, "nature_abstract"])
    
    logger.info(f"Saved ID prompts to {id_path}")
    logger.info(f"Saved OOD prompts to {ood_path}")

def main():
    """
    Entry point for the pilot curation script.
    """
    output_dir = PROJECT_ROOT / "data" / "prompts"
    
    try:
        id_prompts, ood_prompts = curate_pilot_prompts()
        save_prompts(id_prompts, ood_prompts, output_dir)
        logger.info("Pilot curation completed successfully.")
    except SystemExit as e:
        if e.code == 1:
            logger.critical("Pilot curation aborted due to data integrity issues or resource exhaustion.")
            sys.exit(1)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during pilot curation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()