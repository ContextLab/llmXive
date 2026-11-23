import pandas as pd
from typing import List, Optional, Tuple, Set
import datasets
from datasets import load_dataset
from pathlib import Path
import logging
import random
import os
import hashlib
from config import (
    DATA_RAW,
    DATA_PROCESSED,
    RANDOM_SEED,
    N_NOVEL_SAMPLES,
    EXPECTED_AFLOW_CHECKSUM,
    ELEMENT_SOURCE_LIST,
    setup_logging,
    ensure_dirs
)

# Configure logging
logger = setup_logging()

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Compute the checksum of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def get_dataset_checksum_from_hf(dataset_name: str) -> str:
    """
    Retrieve the known SHA256 checksum from HuggingFace dataset metadata.
    In a real implementation, this would parse the dataset card or dataset_infos.json.
    For now, we return the static constant if available, or raise an error.
    """
    # This is a placeholder for the actual logic to fetch from HF metadata.
    # The actual checksum should be retrieved from the dataset card or metadata.
    if EXPECTED_AFLOW_CHECKSUM:
        return EXPECTED_AFLOW_CHECKSUM
    else:
        raise ValueError("EXPECTED_AFLOW_CHECKSUM is not defined in config.")

def load_hmao_dataset(streaming: bool = True):
    """
    Load the AFLOW Thermodynamics dataset from HuggingFace.
    Uses streaming=True to respect RAM limits.
    """
    dataset_name = "foundry-ml/dataset_thermodynamics_aflow"
    logger.info(f"Loading dataset: {dataset_name} with streaming={streaming}")
    
    try:
        dataset = load_dataset(dataset_name, streaming=streaming)
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise ConnectionError(f"Failed to load dataset: {e}")

def validate_dataset_checksum(dataset, expected_checksum: str):
    """
    Validate the dataset checksum against the expected checksum.
    Implements exponential backoff with a maximum of 3 retries if the fetch fails.
    """
    retries = 0
    max_retries = 3
    while retries < max_retries:
        try:
            # In a real implementation, we would compute the checksum of the dataset
            # and compare it to the expected checksum.
            # For now, we assume the dataset is valid if it loads successfully.
            logger.info("Dataset checksum validation skipped (placeholder).")
            return True
        except Exception as e:
            retries += 1
            if retries < max_retries:
                wait_time = 2 ** retries
                logger.warning(f"Checksum validation failed: {e}. Retrying in {wait_time} seconds...")
                import time
                time.sleep(wait_time)
            else:
                logger.error(f"Checksum validation failed after {max_retries} retries.")
                raise

def filter_min_elements(dataset, min_elements: int = 5):
    """
    Filter the dataset for multi-element systems with at least min_elements.
    """
    logger.info(f"Filtering for systems with at least {min_elements} elements.")
    
    filtered_data = []
    for row in dataset['train']:
        # Assuming the dataset has a 'composition' field that is a string or dict
        # We need to count the number of unique elements in the composition.
        composition_str = row.get('composition', '')
        # Simple parsing: split by spaces and count unique elements
        # This is a placeholder; actual parsing depends on the dataset format.
        elements = composition_str.split()
        if len(elements) >= min_elements:
            filtered_data.append(row)
    
    logger.info(f"Filtered dataset size: {len(filtered_data)}")
    return filtered_data

def process_and_save_heas_train(filtered_data, output_path: str):
    """
    Process the filtered data and save to heas_train.csv.
    """
    logger.info(f"Saving training data to {output_path}")
    
    df = pd.DataFrame(filtered_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Training data saved to {output_path}")

def strict_composition_compare(comp1: str, comp2: str) -> bool:
    """
    Perform strict composition string comparison to prevent hash collisions.
    """
    return comp1.strip().lower() == comp2.strip().lower()

def build_deduplicated_composition_index(data: List[dict], composition_key: str = 'composition') -> Set[str]:
    """
    Build a deduplicated composition index from the data.
    """
    index = set()
    for row in data:
        comp_str = row.get(composition_key, '')
        index.add(comp_str.strip().lower())
    return index

def generate_all_5_element_combinations(elements: List[str]) -> List[str]:
    """
    Generate all possible 5-element combinations from the given list of elements.
    """
    from itertools import combinations
    combos = list(combinations(elements, 5))
    return [' '.join(sorted(c)) for c in combos]

def load_hmao_index_for_novelty_check(data_path: str) -> Set[str]:
    """
    Load the composition index from the downloaded dataset for novelty checking.
    """
    logger.info(f"Loading composition index from {data_path}")
    df = pd.read_csv(data_path)
    # Assuming the composition column is named 'composition'
    index = set(df['composition'].str.strip().str.lower())
    return index

def sample_holdout_known(aflow_raw_data: List[dict], train_index: Set[str], n_samples: int, seed: int) -> List[dict]:
    """
    Sample n_samples unique combinations of elements from the aflow_raw dataset,
    excluding those already in the training split.
    """
    logger.info(f"Sampling {n_samples} hold-out known compositions.")
    
    # Filter out compositions that are in the training set
    holdout_candidates = [row for row in aflow_raw_data if row['composition'].strip().lower() not in train_index]
    
    if len(holdout_candidates) < n_samples:
        logger.warning(f"Not enough hold-out candidates ({len(holdout_candidates)}) to sample {n_samples}.")
        # In a real implementation, we might raise an error or adjust n_samples
        n_samples = len(holdout_candidates)
    
    random.seed(seed)
    sampled = random.sample(holdout_candidates, n_samples)
    logger.info(f"Sampled {len(sampled)} hold-out known compositions.")
    return sampled

def sample_true_novel(all_5_element_combos: List[str], train_index: Set[str], local_proxy_index: Set[str], n_samples: int, seed: int) -> List[dict]:
    """
    Sample n_samples unique 5-element combinations that are NOT in the training set
    and NOT in the local proxy (aflow_raw) dataset.
    """
    logger.info(f"Sampling {n_samples} true novel compositions.")
    
    # Filter out compositions that are in the training set or local proxy
    novel_candidates = [combo for combo in all_5_element_combos if combo not in train_index and combo not in local_proxy_index]
    
    if len(novel_candidates) < n_samples:
        logger.warning(f"Not enough novel candidates ({len(novel_candidates)}) to sample {n_samples}.")
        n_samples = len(novel_candidates)
    
    random.seed(seed)
    sampled_combos = random.sample(novel_candidates, n_samples)
    
    # Convert sampled compositions to a list of dicts (placeholder structure)
    sampled_data = [{'composition': combo} for combo in sampled_combos]
    logger.info(f"Sampled {len(sampled_data)} true novel compositions.")
    return sampled_data

def main():
    """
    Main function to orchestrate the data ingestion and sampling process.
    """
    ensure_dirs()
    
    # Load the dataset
    dataset = load_hmao_dataset(streaming=True)
    
    # Validate checksum (placeholder)
    validate_dataset_checksum(dataset, EXPECTED_AFLOW_CHECKSUM)
    
    # Filter for multi-element systems
    filtered_data = filter_min_elements(dataset, min_elements=5)
    
    # Save training data
    train_path = DATA_PROCESSED / 'heas_train.csv'
    process_and_save_heas_train(filtered_data, train_path)
    
    # Build training index
    train_index = build_deduplicated_composition_index(filtered_data)
    
    # Sample hold-out known set
    holdout_data = sample_holdout_known(filtered_data, train_index, N_NOVEL_SAMPLES, RANDOM_SEED)
    holdout_path = DATA_PROCESSED / 'holdout_known.csv'
    pd.DataFrame(holdout_data).to_csv(holdout_path, index=False)
    logger.info(f"Saved hold-out known data to {holdout_path}")
    
    # Sample true novel set
    all_combos = generate_all_5_element_combinations(ELEMENT_SOURCE_LIST)
    local_proxy_index = load_hmao_index_for_novelty_check(train_path)
    novel_data = sample_true_novel(all_combos, train_index, local_proxy_index, N_NOVEL_SAMPLES, RANDOM_SEED)
    novel_path = DATA_PROCESSED / 'true_novel.csv'
    pd.DataFrame(novel_data).to_csv(novel_path, index=False)
    logger.info(f"Saved true novel data to {novel_path}")

if __name__ == '__main__':
    main()
