"""
Data Splitting Module for BMG Shear Modulus Prediction.

Implements stratified train/test split by alloy family as per FR-004.
Ensures that the distribution of alloy families is preserved across train and test sets.
"""
import os
import sys
import logging
import csv
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_SEED = 42
MIN_FAMILY_SIZE = 2  # Minimum samples in a family to consider for stratification

def load_processed_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the processed dataset from a CSV file.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        List of dictionaries representing the rows.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to float where appropriate
            processed_row = {}
            for key, value in row.items():
                try:
                    processed_row[key] = float(value)
                except (ValueError, TypeError):
                    processed_row[key] = value
            data.append(processed_row)
    
    logger.info(f"Loaded {len(data)} records from {input_path}")
    return data

def extract_alloy_family(row: Dict[str, Any]) -> str:
    """
    Extract the alloy family from a data row.
    
    Assumes the 'composition' or 'system' column contains the family information.
    If 'family' column exists, use that. Otherwise, derive from composition.
    
    Args:
        row: A single data row.
        
    Returns:
        The alloy family string.
    """
    if 'family' in row:
        return str(row['family'])
    
    # Fallback: try to derive from composition or system
    if 'system' in row:
        return str(row['system'])
    
    if 'composition' in row:
        # Simple heuristic: take the first element or a substring
        # This assumes composition is formatted like "Zr-Cu-Al"
        comp_str = str(row['composition'])
        if '-' in comp_str:
            return comp_str.split('-')[0]
        return comp_str
    
    raise ValueError("Could not determine alloy family from row: no 'family', 'system', or 'composition' column found.")

def stratified_split(
    data: List[Dict[str, Any]],
    test_size: float = DEFAULT_TEST_SIZE,
    random_seed: int = DEFAULT_RANDOM_SEED,
    family_column: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Perform a stratified train/test split based on alloy family.
    
    Groups data by family, then splits each group proportionally.
    Ensures that small families (size < MIN_FAMILY_SIZE) are kept in train only
    to avoid empty test sets or unstable metrics, unless forced.
    
    Args:
        data: List of data records.
        test_size: Proportion of data to include in the test set.
        random_seed: Seed for random number generator.
        family_column: Name of the column containing family info. If None, inferred.
        
    Returns:
        Tuple of (train_data, test_data).
    """
    random.seed(random_seed)
    
    # Group data by family
    families: Dict[str, List[Dict[str, Any]]] = {}
    for row in data:
        family = extract_alloy_family(row) if family_column is None else str(row.get(family_column, "Unknown"))
        if family not in families:
            families[family] = []
        families[family].append(row)
    
    logger.info(f"Found {len(families)} unique alloy families.")
    
    train_data = []
    test_data = []
    
    for family, members in families.items():
        n_total = len(members)
        
        # If family is too small, put all in train to avoid empty test splits
        if n_total < MIN_FAMILY_SIZE:
            logger.debug(f"Family '{family}' has only {n_total} samples. Keeping in train set.")
            train_data.extend(members)
            continue
        
        # Shuffle the family members
        shuffled = members.copy()
        random.shuffle(shuffled)
        
        # Calculate split index
        n_test = max(1, int(n_total * test_size))
        # Ensure we don't take all samples for test if n_total is small
        if n_test >= n_total:
            n_test = max(1, n_total - 1)
        
        split_idx = n_total - n_test
        
        train_data.extend(shuffled[:split_idx])
        test_data.extend(shuffled[split_idx:])
    
    logger.info(f"Split complete: Train={len(train_data)}, Test={len(test_data)}")
    
    # Verify stratification roughly
    train_families = {}
    test_families = {}
    for row in train_data:
        f = extract_alloy_family(row) if family_column is None else str(row.get(family_column, "Unknown"))
        train_families[f] = train_families.get(f, 0) + 1
    
    for row in test_data:
        f = extract_alloy_family(row) if family_column is None else str(row.get(family_column, "Unknown"))
        test_families[f] = test_families.get(f, 0) + 1
    
    logger.debug(f"Train family distribution: {train_families}")
    logger.debug(f"Test family distribution: {test_families}")
    
    return train_data, test_data

def save_split_data(
    train_data: List[Dict[str, Any]],
    test_data: List[Dict[str, Any]],
    train_path: Path,
    test_path: Path
) -> None:
    """
    Save the train and test splits to CSV files.
    
    Args:
        train_data: List of train records.
        test_data: List of test records.
        train_path: Output path for train CSV.
        test_path: Output path for test CSV.
    """
    if not train_data and not test_data:
        raise ValueError("No data to save. Check the split logic.")
    
    # Combine all data to get headers
    all_data = train_data + test_data
    if not all_data:
        return
    
    headers = list(all_data[0].keys())
    
    def write_csv(data: List[Dict[str, Any]], path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Saved {len(data)} records to {path}")
    
    write_csv(train_data, train_path)
    write_csv(test_data, test_path)

def main():
    """
    Main entry point for the data splitting script.
    
    Reads from data/processed/cleaned_bmg_features.csv and outputs:
    - data/processed/train_split.csv
    - data/processed/test_split.csv
    """
    # Configuration
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / "data" / "processed" / "cleaned_bmg_features.csv"
    train_output = project_root / "data" / "processed" / "train_split.csv"
    test_output = project_root / "data" / "processed" / "test_split.csv"
    
    test_size = float(os.getenv("TEST_SIZE", "0.2"))
    random_seed = int(os.getenv("RANDOM_SEED", "42"))
    
    logger.info(f"Starting data split with test_size={test_size}, seed={random_seed}")
    
    try:
        # Load data
        data = load_processed_data(input_file)
        
        if len(data) == 0:
            raise ValueError("Input data is empty. Cannot perform split.")
        
        # Perform split
        train_data, test_data = stratified_split(
            data,
            test_size=test_size,
            random_seed=random_seed
        )
        
        if len(test_data) == 0:
            logger.warning("Test set is empty. All data may have been assigned to train due to small family sizes.")
        
        # Save results
        save_split_data(train_data, test_data, train_output, test_output)
        
        logger.info("Data splitting completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during data splitting: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    configure_root_logger = get_logger("split_main") # Just to ensure logging is ready if not configured
    main()