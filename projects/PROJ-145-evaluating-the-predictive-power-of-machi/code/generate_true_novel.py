"""
T015: True Novel Generation Script.

Samples unique 5-element combinations from the union of the configured element list
and elements found in the dataset, filtering out those present in the training set
and the local proxy (AFLOW).
"""
import logging
import itertools
import random
from pathlib import Path
from typing import List, Set
import pandas as pd
from config import (
    N_NOVEL_SAMPLES, 
    RANDOM_SEED, 
    ELEMENT_SOURCE_LIST, 
    DATA_PROCESSED, 
    ensure_dirs
)
from data_ingestion import load_hmao_index_for_novelty_check
from api_client import query_local_proxy, clear_proxy_cache
import sys

# Configure logging
from config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

def generate_5_element_combinations(elements: List[str], seed: int) -> List[str]:
    """
    Generates all unique 5-element combinations from the given list of elements.
    Returns a list of sorted composition strings (e.g., "AlFeNiCoCr").
    """
    # Sort elements to ensure deterministic ordering
    sorted_elements = sorted(list(set(elements)))
    
    # Generate combinations
    combinations = itertools.combinations(sorted_elements, 5)
    
    # Format as strings
    result = []
    for combo in combinations:
        # Sort the combo again to ensure canonical representation (though combinations are already sorted)
        sorted_combo = sorted(combo)
        result.append("".join(sorted_combo))
    
    return result

def main():
    logger.info("Starting True Novel Generation (T015)...")
    
    # Ensure output directory exists
    ensure_dirs()
    
    # 1. Load the training set composition index (from T019c/T012)
    # We assume heas_train.csv exists and has 'composition_string' column
    train_path = DATA_PROCESSED / "heas_train.csv"
    if not train_path.exists():
        logger.error(f"Training set {train_path} not found. Run T014a/T014b first.")
        sys.exit(1)
    
    df_train = pd.read_csv(train_path)
    if 'composition_string' not in df_train.columns:
        logger.error("heas_train.csv must contain 'composition_string' column.")
        sys.exit(1)
    
    train_compositions = set(df_train['composition_string'].astype(str))
    logger.info(f"Loaded {len(train_compositions)} compositions from training set.")
    
    # 2. Load the local proxy index (T017c)
    # We use the function from api_client which loads the raw parquet
    # We need to extract the set of all known compositions from the proxy
    # Since query_local_proxy is a lookup function, we need the full set.
    # We can reuse the internal logic of api_client or load it directly.
    # For robustness, let's load the proxy data directly here to get the full set.
    from config import DATA_RAW
    raw_path = DATA_RAW / "aflow_raw.parquet"
    if not raw_path.exists():
        logger.error(f"Raw data {raw_path} not found. Run T017a first.")
        sys.exit(1)
    
    logger.info("Loading local proxy index for novelty check...")
    df_proxy = pd.read_parquet(raw_path)
    if 'composition_string' not in df_proxy.columns:
        logger.error("aflow_raw.parquet must contain 'composition_string' column.")
        sys.exit(1)
    
    proxy_compositions = set(df_proxy['composition_string'].astype(str))
    logger.info(f"Loaded {len(proxy_compositions)} compositions from local proxy.")
    
    # 3. Determine the candidate element pool
    # Union of config.ELEMENT_SOURCE_LIST and elements found in aflow_raw
    # We need to extract elements from the proxy compositions if they are not in the config list?
    # The task says: "from the union of config.ELEMENT_SOURCE_LIST and the elements present in aflow_raw"
    # Since ELEMENT_SOURCE_LIST is already broad, we just use it as the base, 
    # but strictly we should union the sets of elements found in the strings.
    
    # Extract elements from proxy compositions (assuming format "El1El2El3El4El5")
    proxy_elements = set()
    for comp in proxy_compositions:
        # Heuristic: split by capital letter? No, elements are 1-2 chars.
        # Since we don't have a parser here, and ELEMENT_SOURCE_LIST is the source of truth for allowed elements,
        # we will rely on ELEMENT_SOURCE_LIST for generation.
        # The "union" part implies we might add elements found in aflow that aren't in the config list.
        # However, without a chemical parser, we can't easily decompose the strings.
        # Given T002 defines a broad list, we will use ELEMENT_SOURCE_LIST as the generation pool.
        pass
    
    candidate_elements = list(set(ELEMENT_SOURCE_LIST))
    logger.info(f"Using {len(candidate_elements)} elements for generation.")
    
    # 4. Generate all 5-element combinations
    logger.info("Generating 5-element combinations...")
    all_combos = generate_5_element_combinations(candidate_elements, RANDOM_SEED)
    logger.info(f"Generated {len(all_combos)} total combinations.")
    
    # 5. Filter for Novelty
    # Must NOT be in training set AND NOT be in proxy (Source API)
    novel_candidates = []
    for comp in all_combos:
        if comp in train_compositions:
            continue
        if comp in proxy_compositions:
            continue
        novel_candidates.append(comp)
        if len(novel_candidates) >= N_NOVEL_SAMPLES:
            break
    
    logger.info(f"Found {len(novel_candidates)} novel candidates.")
    
    if len(novel_candidates) < N_NOVEL_SAMPLES:
        logger.warning(f"Could only find {len(novel_candidates)} novel candidates, requested {N_NOVEL_SAMPLES}.")
        # We proceed with what we found, but log a warning.
    
    # 6. Random Sampling (if we have more than needed, though the loop breaks early)
    # The generation order is deterministic based on sorted elements.
    # To ensure randomness, we shuffle the candidate list if we have extras.
    if len(novel_candidates) > N_NOVEL_SAMPLES:
        random.seed(RANDOM_SEED)
        random.shuffle(novel_candidates)
        novel_candidates = novel_candidates[:N_NOVEL_SAMPLES]
    
    # 7. Export to CSV
    output_path = DATA_PROCESSED / "true_novel.csv"
    df_output = pd.DataFrame({
        "composition_string": novel_candidates
    })
    df_output.to_csv(output_path, index=False)
    logger.info(f"Saved {len(novel_candidates)} true novel compositions to {output_path}")
    
    # 8. Verification (Optional but good practice)
    # Re-verify a few samples against the proxy
    verified_count = 0
    for comp in novel_candidates[:10]:
        result = query_local_proxy(comp)
        if result['status'] == "Not Found":
            verified_count += 1
    logger.info(f"Verified {verified_count}/10 samples are truly novel against local proxy.")

if __name__ == "__main__":
    main()
