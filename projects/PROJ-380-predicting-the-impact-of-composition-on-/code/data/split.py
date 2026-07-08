import os
import sys
import logging
import csv
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> List[Dict[str, Any]]:
    """Load CSV data into list of dicts."""
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def extract_alloy_family(composition: str) -> str:
    """
    Extract dominant alloy family from composition string (e.g., 'Zr50...' -> 'Zr').
    """
    # Simple heuristic: take the first element symbol
    if not composition:
        return "Unknown"
    return composition[:2] if composition[1].isupper() else composition[:1]

def stratified_split(data: List[Dict[str, Any]], target_col: str, test_size: float = 0.2, seed: int = 42) -> tuple[List[Dict], List[Dict]]:
    """
    Perform stratified train/test split based on alloy family.
    """
    random.seed(seed)
    # Group by family
    families = {}
    for row in data:
        fam = extract_alloy_family(row.get('composition', ''))
        if fam not in families:
            families[fam] = []
        families[fam].append(row)
    
    train, test = [], []
    for fam, rows in families.items():
        random.shuffle(rows)
        split_idx = int(len(rows) * (1 - test_size))
        train.extend(rows[:split_idx])
        test.extend(rows[split_idx:])
    
    return train, test

def save_split_data(train: List[Dict], test: List[Dict], train_path: str, test_path: str):
    """Save train and test splits to CSV."""
    def write(path, rows):
        if not rows:
            return
        fieldnames = rows[0].keys()
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    write(train_path, train)
    write(test_path, test)
    logger.info(f"Saved train ({len(train)}) to {train_path}")
    logger.info(f"Saved test ({len(test)}) to {test_path}")

def main():
    """Entry point for splitting."""
    input_file = "data/processed/processed_bmg_features.csv"
    train_file = "data/processed/train.csv"
    test_file = "data/processed/test.csv"
    
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        train_file = sys.argv[2]
    if len(sys.argv) >= 4:
        test_file = sys.argv[3]
        
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
        
    data = load_processed_data(input_file)
    train, test = stratified_split(data, target_col='shear_modulus_gpa')
    save_split_data(train, test, train_file, test_file)

if __name__ == "__main__":
    main()
