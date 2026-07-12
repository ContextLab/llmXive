import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from datasets import load_dataset

# Add code directory to path if running from project root
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from config import (
    DATA_RAW_DIR, DATASET_NAME, SMILES_COL, CID_COL,
    SAMPLE_SIZE, RANDOM_SEED, RAW_DATA_FILE
)
from logging_setup import setup_logging, log_skipped_molecule, log_data_loading_stats

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_and_sample_dataset() -> Dict[str, Any]:
    """
    Load the HuggingFace dataset, apply stratified random sampling to prevent memory overflow,
    validate SMILES, and save to disk.
    
    This implementation uses streaming to avoid loading the full dataset into RAM.
    It performs stratified sampling based on a hash of the SMILES string to ensure
    reproducibility and distribution across the dataset.
    
    Returns:
        A dictionary with statistics about the loading process.
    """
    logger = setup_logging()
    logger.info(f"Loading dataset: {DATASET_NAME}")
    
    start_time = time.time()
    total_loaded = 0
    valid_count = 0
    skipped_count = 0
    
    # We will collect samples in a list until we reach SAMPLE_SIZE
    # To perform stratified sampling without loading everything, we use a reservoir sampling approach
    # combined with a hash-based strata assignment.
    # Since we cannot load the whole dataset, we stream it.
    
    # Load dataset in streaming mode
    try:
        dataset = load_dataset(DATASET_NAME, split="train", streaming=True)
        
        # Check for required columns in the streaming dataset
        # We need to peek at the schema or try to access an item
        try:
            first_item = next(iter(dataset))
        except StopIteration:
            raise ValueError("Dataset is empty")
        
        if SMILES_COL not in first_item or CID_COL not in first_item:
            raise ValueError(f"Dataset missing required columns: {SMILES_COL}, {CID_COL}")
        
        # Reservoir sampling with stratification
        # We assign each item to a stratum based on hash(SMILES) % NUM_STRATA
        # Then we sample proportionally from each stratum.
        # However, true stratified sampling requires knowing the total count per stratum.
        # Given the memory constraint, we use a two-pass approach if feasible,
        # or a weighted reservoir sampling.
        # For this implementation, we will use a simplified approach:
        # 1. Stream through the dataset.
        # 2. Assign each valid item to a "bucket" based on a hash of the SMILES.
        # 3. Maintain a reservoir for each bucket to ensure we get a representative sample.
        
        NUM_STRATA = 100
        reservoirs: Dict[int, list] = {i: [] for i in range(NUM_STRATA)}
        counts_per_stratum: Dict[int, int] = {i: 0 for i in range(NUM_STRATA)}
        
        for item in dataset:
            total_loaded += 1
            smiles = item.get(SMILES_COL)
            cid = item.get(CID_COL)
            
            # Validate SMILES
            if smiles is None or not isinstance(smiles, str) or smiles == "":
                skipped_count += 1
                continue
            
            # Determine stratum based on hash of SMILES
            stratum = int(hashlib.md5(smiles.encode()).hexdigest(), 16) % NUM_STRATA
            counts_per_stratum[stratum] += 1
            
            # Reservoir sampling for this stratum
            # We want to sample roughly SAMPLE_SIZE / NUM_STRATA from each stratum
            target_per_stratum = SAMPLE_SIZE // NUM_STRATA
            reservoir = reservoirs[stratum]
            
            if len(reservoir) < target_per_stratum:
                reservoir.append(item)
            else:
                # Replace with probability (target / current_count)
                # This is a simplified reservoir sampling for fixed size
                import random
                j = random.randint(0, counts_per_stratum[stratum] - 1)
                if j < target_per_stratum:
                    reservoir[j] = item
        
        # Collect all sampled items
        sampled_items = []
        for reservoir in reservoirs.values():
            sampled_items.extend(reservoir)
        
        # If we have more than SAMPLE_SIZE (due to rounding), trim
        if len(sampled_items) > SAMPLE_SIZE:
            import random
            sampled_items = random.sample(sampled_items, SAMPLE_SIZE)
        
        # Convert to DataFrame
        df_sampled = pd.DataFrame(sampled_items)
        valid_count = len(df_sampled)
        
        duration = time.time() - start_time
        logger.info(f"Streamed {total_loaded} molecules, sampled {valid_count} in {duration:.2f}s.")
        
        # Save to parquet
        output_path = str(RAW_DATA_FILE)
        df_sampled.to_parquet(output_path, index=False)
        logger.info(f"Saved {valid_count} molecules to {output_path}")
        
        stats = {
            "total_loaded": total_loaded,
            "total_sampled": valid_count,
            "skipped_invalid": skipped_count,
            "duration_seconds": duration
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def main():
    """Entry point for download script."""
    stats = load_and_sample_dataset()
    checksum = compute_file_checksum(str(RAW_DATA_FILE))
    
    # Log stats using the new logging function
    log_data_loading_stats(
        total_loaded=stats["total_loaded"],
        total_sampled=stats["total_sampled"],
        checksum=checksum,
        duration_seconds=stats.get("duration_seconds", 0.0)
    )
    
    return stats

if __name__ == "__main__":
    main()
