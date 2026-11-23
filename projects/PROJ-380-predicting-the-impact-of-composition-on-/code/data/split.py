import os
import sys
import logging
import csv
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> List[Dict[str, Any]]:
    """Load CSV data into list of dicts."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def extract_alloy_family(composition: str) -> str:
    """
    Extract dominant alloy family from composition string (e.g., 'Zr50...' -> 'Zr').
    Handles cases like 'Zr40Cu40Ag20' -> 'Zr', 'Pd77Si16Cu7' -> 'Pd'.
    """
    if not composition or not composition.strip():
        return "Unknown"
    
    # Clean composition string
    comp_str = composition.strip()
    
    # Find the first element symbol (1 or 2 uppercase letters followed by lowercase or digit)
    i = 0
    while i < len(comp_str):
        if comp_str[i].isupper():
            # Check if next char is lowercase (2-letter symbol)
            if i + 1 < len(comp_str) and comp_str[i+1].islower():
                return comp_str[i:i+2]
            else:
                return comp_str[i]
        i += 1
    
    return "Unknown"

def hybrid_stratified_split(
    data: List[Dict[str, Any]], 
    target_col: str = 'shear_modulus_gpa',
    test_size: float = 0.2,
    seed: int = 42,
    small_family_threshold: int = 10,
    gkf_k: int = 5
) -> Tuple[List[Dict], List[Dict]]:
    """
    Perform hybrid stratified train/test split by alloy family.
    
    Logic:
    - Families with >= small_family_threshold samples: Standard stratified split.
    - Families with < small_family_threshold samples: Use GroupKFold-like logic
      to ensure they are included in the validation set, but for a single split
      we distribute them proportionally or ensure representation.
    
    Since we need a single train/test split (not cross-validation folds) for the
    main pipeline, we adapt the logic:
    - For large families: Standard stratified split.
    - For small families: We still split but ensure the split ratio is respected,
      acknowledging that with very small N, the split might be 0/1 or 1/0.
      We do NOT exclude them.
    
    The "LOFO" and "GroupKFold" strategies mentioned in the task are primarily
    for the evaluation phase (T030) where cross-validation is performed.
    Here, for the initial data split, we perform a stratified split that
    respects family boundaries as much as possible.
    """
    random.seed(seed)
    
    # Group by family
    families: Dict[str, List[Dict[str, Any]]] = {}
    for row in data:
        fam = extract_alloy_family(row.get('composition', ''))
        if fam not in families:
            families[fam] = []
        families[fam].append(row)
    
    train: List[Dict[str, Any]] = []
    test: List[Dict[str, Any]] = []
    
    stats = []
    
    for fam, rows in families.items():
        n = len(rows)
        is_small = n < small_family_threshold
        
        # Shuffle rows within family
        shuffled_rows = rows.copy()
        random.shuffle(shuffled_rows)
        
        # Calculate split index
        # For small families, we still try to respect the ratio, but ensure at least 1 in test if possible
        split_idx = int(n * (1 - test_size))
        
        # Ensure we don't end up with 0 test samples for small families if n > 0
        if is_small and n > 0:
            if split_idx == n:
                split_idx = n - 1
            if split_idx < 0:
                split_idx = 0
        
        fam_train = shuffled_rows[:split_idx]
        fam_test = shuffled_rows[split_idx:]
        
        train.extend(fam_train)
        test.extend(fam_test)
        
        stats.append({
            "family": fam,
            "total": n,
            "train": len(fam_train),
            "test": len(fam_test),
            "is_small": is_small
        })
        
        logger.debug(f"Family {fam}: n={n}, train={len(fam_train)}, test={len(fam_test)} (small={is_small})")
    
    logger.info(f"Hybrid split completed. Total samples: {len(data)}, Train: {len(train)}, Test: {len(test)}")
    for stat in stats:
        if stat['is_small']:
            logger.info(f"Small family {stat['family']} handled: {stat['train']} train, {stat['test']} test")
    
    return train, test

def save_split_data(train: List[Dict], test: List[Dict], train_path: str, test_path: str):
    """Save train and test splits to CSV."""
    def write(path, rows):
        if not rows:
            logger.warning(f"Attempting to write empty split to {path}")
            # Write header only if we can determine fieldnames, otherwise skip
            return 
        fieldnames = rows[0].keys()
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"Saved {len(rows)} rows to {path}")
    
    write(train_path, train)
    write(test_path, test)

def main():
    """Entry point for splitting."""
    # Default paths relative to project root
    input_file = "data/processed/processed_bmg_features.csv"
    train_file = "data/processed/train.csv"
    test_file = "data/processed/test.csv"
    
    # Allow CLI overrides
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        train_file = sys.argv[2]
    if len(sys.argv) >= 4:
        test_file = sys.argv[3]
        
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
        
    logger.info(f"Loading processed data from {input_file}")
    data = load_processed_data(input_file)
    
    if not data:
        logger.error("Input data is empty.")
        sys.exit(1)
    
    logger.info(f"Performing hybrid stratified split on {len(data)} samples")
    train, test = hybrid_stratified_split(data, target_col='shear_modulus_gpa')
    
    if not train:
        logger.error("Train split is empty.")
        sys.exit(1)
    if not test:
        logger.error("Test split is empty.")
        sys.exit(1)
    
    save_split_data(train, test, train_file, test_file)
    logger.info("Splitting complete.")

if __name__ == "__main__":
    main()