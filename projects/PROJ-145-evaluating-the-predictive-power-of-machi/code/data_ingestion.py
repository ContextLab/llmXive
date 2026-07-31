import pandas as pd
from typing import List, Optional, Tuple
import datasets
from pathlib import Path
import logging
import os
from itertools import combinations
import random
import hashlib
from collections import Counter

# Import from config if needed for paths, though we use standard paths here
# Assuming config.py sets up logging and directories, we ensure they exist here too if needed.
# However, the task specifically asks to implement the logic in this file.

logger = logging.getLogger(__name__)

# Constants for reproducibility
RANDOM_SEED = 42
N_NOVEL_SAMPLES = 5000
MIN_ELEMENTS = 5
NUM_ELEMENTS_IN_PERIODIC_TABLE = 118  # Standard count

def load_hmao_dataset(streaming: bool = True):
    """
    Load the hmao/all_apis_for_multiapi dataset.
    """
    logger.info("Loading hmao/all_apis_for_multiapi dataset...")
    try:
        dataset = datasets.load_dataset("hmao/all_apis_for_multiapi", split="train", streaming=streaming)
        logger.info("Dataset loaded successfully.")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def filter_min_elements(dataset, min_elements: int = 5) -> datasets.IterableDataset:
    """
    Filter the dataset to keep only systems with >= min_elements.
    """
    def condition(example):
        # The 'elements' field is expected to be a list or string representation of elements.
        # Based on typical HEA datasets, it might be a list of element symbols.
        # We need to handle both list and string cases if necessary.
        elements = example.get('elements', [])
        if isinstance(elements, str):
            # If it's a string like "Fe,Co,Ni", split it
            elements = [e.strip() for e in elements.split(',')]
        
        return len(elements) >= min_elements

    return dataset.filter(condition)

def process_and_save_heas_train(dataset, output_path: str = "data/processed/heas_train.csv"):
    """
    Process the dataset, map columns, and save to CSV.
    """
    logger.info("Processing and saving HEAs train data...")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define column mapping
    # Assuming the dataset has 'formation_energy_per_atom' and 'mixing_enthalpy'
    # We map them to 'target_energy' and 'target_hmix'
    # Also need 'elements' and 'composition_string' for novelty checks later
    
    # We will iterate and collect rows
    rows = []
    count = 0
    
    for item in dataset:
        # Map fields
        # Handle potential missing keys gracefully
        energy = item.get('formation_energy_per_atom')
        hmix = item.get('mixing_enthalpy')
        elements = item.get('elements', [])
        comp_str = item.get('composition_string', '')
        
        # If elements is a list, join it to a canonical string for comparison
        if isinstance(elements, list):
            # Sort to ensure canonical representation if not already
            sorted_elements = sorted(elements)
            canonical_elements = ','.join(sorted_elements)
        else:
            canonical_elements = elements
        
        rows.append({
            'target_energy': energy,
            'target_hmix': hmix,
            'elements': canonical_elements,
            'composition_string': comp_str
        })
        
        count += 1
        if count % 10000 == 0:
            logger.info(f"Processed {count} rows...")
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")
    return df

def generate_all_5_element_combinations() -> List[Tuple[str, ...]]:
    """
    Generate all unique 5-element combinations from the periodic table.
    This is computationally expensive (C(118, 5) = ~10 million), so we must sample.
    However, the task asks to SAMPLE 5000 unique combinations.
    To do this correctly, we need a list of all element symbols.
    We will use a hardcoded list of the first 118 elements (or a subset if we only care about stable ones).
    For this task, we assume standard elements 1-118.
    """
    # Standard element symbols (1-118)
    # This list is standard and static.
    elements = [
        "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
        "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
        "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
        "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
        "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
        "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
        "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb",
        "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
        "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th",
        "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm",
        "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds",
        "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"
    ]
    
    if len(elements) < 5:
        raise ValueError("Not enough elements to form 5-element combinations.")
    
    # We need to sample 5000 unique combinations.
    # Total combinations = C(118, 5) = 118! / (5! * 113!) = 10,000,000+
    # We cannot generate all and then sample if memory is tight, but 10M tuples is manageable in RAM (approx 1-2GB).
    # However, to be safe and efficient, we can use random.sample on the iterator if we could, but random.sample needs a sequence.
    # Given the constraints, generating all combinations might be too slow/memory heavy for a quick script if not careful.
    # But C(118, 5) is ~10 million. Generating 10 million tuples in a list might take ~1-2 seconds and ~1GB RAM.
    # Let's try to generate them and sample.
    
    logger.info(f"Generating all {len(elements)} element combinations (C({len(elements)}, 5) is large)...")
    
    # We use a fixed seed for reproducibility
    random.seed(RANDOM_SEED)
    
    # To avoid generating 10M items in memory if not needed, we can try to sample indices.
    # But itertools.combinations returns an iterator.
    # We can convert to list if memory permits, or use a reservoir sampling if we wanted a random subset without generating all.
    # However, the task says "Sample 5000 unique 5-element combinations".
    # The most straightforward way to ensure uniqueness and randomness is to generate all and pick.
    # If memory is an issue, we can use a set to store sampled ones until we have 5000.
    
    # Let's try to generate all combinations and sample.
    # If this is too slow, we can optimize.
    # Given the 300s budget, generating 10M items might be borderline.
    # Let's try a different approach: generate random combinations until we have 5000 unique ones.
    # This is O(N) where N is the number of attempts. With 10M total, 5000 is small.
    # Probability of collision is low.
    
    unique_combos = set()
    attempts = 0
    max_attempts = 1000000 # Safety limit
    
    while len(unique_combos) < N_NOVEL_SAMPLES and attempts < max_attempts:
        combo = tuple(sorted(random.sample(elements, 5)))
        unique_combos.add(combo)
        attempts += 1
    
    if len(unique_combos) < N_NOVEL_SAMPLES:
        logger.warning(f"Could not generate {N_NOVEL_SAMPLES} unique combinations after {attempts} attempts.")
        # If we failed, we have what we have.
    
    return [tuple(c) for c in unique_combos]

def load_hmao_index_for_novelty_check(dataset) -> set:
    """
    Load the set of composition strings (or element combinations) from the hmao dataset
    to serve as the 'proxy index' for novelty verification.
    We need to check if a sampled combination is 'present' in the hmao dataset.
    The task says: "Filter for those present in the hmao proxy index".
    So we need to build a set of known combinations from the hmao dataset.
    
    We assume the 'elements' field in the dataset represents the combination.
    We will canonicalize it (sorted, comma-separated) to match our generated samples.
    """
    logger.info("Building hmao proxy index for novelty check...")
    known_combos = set()
    count = 0
    
    # We stream through the dataset to build the index
    for item in dataset:
        elements = item.get('elements', [])
        if isinstance(elements, str):
            elements = [e.strip() for e in elements.split(',')]
        
        if isinstance(elements, list):
            sorted_elements = sorted(elements)
            canonical = ','.join(sorted_elements)
            # We only care about 5-element systems for this check?
            # The task says "5-element combinations". So we only index 5-element ones.
            if len(sorted_elements) == 5:
                known_combos.add(canonical)
        
        count += 1
        if count % 50000 == 0:
            logger.info(f"Indexed {count} rows, {len(known_combos)} unique 5-element combos...")
    
    logger.info(f"Built proxy index with {len(known_combos)} unique 5-element combinations.")
    return known_combos

def sample_holdout_known(hmao_dataset, train_df, output_path: str = "data/processed/holdout_known.csv"):
    """
    Sample 5000 unique 5-element combinations that are:
    1. Present in the hmao proxy index (hmao_dataset)
    2. NOT present in heas_train.csv (train_df)
    
    This requires:
    - Building the hmao proxy index (set of canonical 5-element strings)
    - Building the train index (set of canonical 5-element strings from train_df)
    - Generating 5000 random 5-element combinations
    - Filtering those that are in hmao index AND not in train index
    - If we don't get 5000, we might need to generate more or report error.
    """
    logger.info("Starting holdout known sampling...")
    
    # 1. Build hmao proxy index
    hmao_index = load_hmao_index_for_novelty_check(hmao_dataset)
    
    # 2. Build train index
    train_index = set()
    if 'elements' in train_df.columns:
        for elem_str in train_df['elements']:
            # elem_str is already canonical (sorted, comma-separated) from process_and_save_heas_train
            # But let's ensure it's 5 elements
            parts = elem_str.split(',')
            if len(parts) == 5:
                train_index.add(elem_str)
    else:
        logger.error("train_df does not have 'elements' column.")
        return

    logger.info(f"Train index size: {len(train_index)}")
    logger.info(f"HMAO index size: {len(hmao_index)}")
    
    # 3. Generate random 5-element combinations
    # We need to sample from the periodic table
    # Re-use the generation logic
    elements_list = [
        "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
        "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
        "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
        "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
        "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
        "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
        "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb",
        "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
        "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th",
        "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm",
        "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds",
        "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"
    ]
    
    random.seed(RANDOM_SEED)
    
    candidate_combos = []
    attempts = 0
    max_attempts = 10000000 # Safety limit
    
    while len(candidate_combos) < N_NOVEL_SAMPLES and attempts < max_attempts:
        combo = tuple(sorted(random.sample(elements_list, 5)))
        canonical = ','.join(combo)
        
        # Check conditions:
        # 1. In hmao index
        # 2. Not in train index
        if canonical in hmao_index and canonical not in train_index:
            candidate_combos.append(canonical)
        
        attempts += 1
        if attempts % 100000 == 0:
            logger.info(f"Attempts: {attempts}, Found: {len(candidate_combos)}")
    
    if len(candidate_combos) < N_NOVEL_SAMPLES:
        logger.error(f"Failed to find {N_NOVEL_SAMPLES} unique holdout known combinations. Found {len(candidate_combos)}.")
        # We proceed with what we have, but this is a failure condition ideally.
        # The task says "Filter for those present...". If not enough exist, we can't make 5000.
        # We will save what we found.
    
    # Create DataFrame
    df_holdout = pd.DataFrame(candidate_combos, columns=['composition_string'])
    # We might want to add other columns if needed, but the task just says "Export to ...".
    # The columns should match the expected output format if any.
    # Let's assume just composition_string is enough for now, or maybe we need to fetch data?
    # The task says "Filter for those present in the hmao proxy index". It doesn't say to fetch their properties.
    # So just the composition string is likely sufficient.
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_holdout.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df_holdout)} rows to {output_path}")
    return df_holdout

def main():
    """
    Main entry point for T014 implementation.
    This function orchestrates the loading, filtering, and sampling for holdout_known.csv.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Load dataset
    dataset = load_hmao_dataset(streaming=True)
    
    # We need the train_df to check what's already in heas_train.csv
    # We assume T013 has already run and produced data/processed/heas_train.csv
    train_path = "data/processed/heas_train.csv"
    if not os.path.exists(train_path):
        logger.error(f"Train file {train_path} not found. Please run T013 first.")
        return
    
    train_df = pd.read_csv(train_path)
    
    # Sample holdout known
    sample_holdout_known(dataset, train_df, "data/processed/holdout_known.csv")

if __name__ == "__main__":
    main()
