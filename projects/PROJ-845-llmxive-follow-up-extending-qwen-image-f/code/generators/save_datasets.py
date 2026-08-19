"""
T016 Implementation: Save generated CSVs to data/raw/

This script orchestrates the generation and saving of the four required datasets:
high_entropy.csv, low_entropy.csv, target_specific.csv, and test_set.csv.

It relies on the logic_generator, contradiction_checker, and dataset_saver modules
which are assumed to be implemented in other tasks.
"""
import os
import sys
import argparse
import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config, get_config
from utils.logger import get_logger
from generators.logic_generator import generate_dataset_batch
from generators.contradiction_checker import is_problem_solvable, filter_contradictions
from generators.dataset_saver import ensure_data_dir, problem_to_row, save_problems_to_csv

logger = get_logger(__name__)

# Constants for file paths
DATA_RAW_DIR = project_root / "data" / "raw"
FILE_HIGH = DATA_RAW_DIR / "high_entropy.csv"
FILE_LOW = DATA_RAW_DIR / "low_entropy.csv"
FILE_TARGET = DATA_RAW_DIR / "target_specific.csv"
FILE_TEST = DATA_RAW_DIR / "test_set.csv"

# Required columns matching SyntheticProblem schema + extras
REQUIRED_COLUMNS = [
    "id", "premises", "operators", "solution", "entropy_level", 
    "structure_hash", "set_type", "metadata"
]

def load_existing_hashes() -> Set[str]:
    """Load structure hashes from existing CSVs to ensure distinctness."""
    existing_hashes: Set[str] = set()
    csv_files = [FILE_HIGH, FILE_LOW, FILE_TARGET]
    
    for f_path in csv_files:
        if f_path.exists():
            logger.info(f"Loading existing hashes from {f_path.name}...")
            with open(f_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'structure_hash' in row and row['structure_hash']:
                        existing_hashes.add(row['structure_hash'])
    return existing_hashes

def generate_and_save_subset(
    subset_name: str,
    target_count: int,
    entropy_level: str,
    existing_hashes: Set[str]
) -> List[Dict[str, Any]]:
    """
    Generate a specific subset of problems ensuring solvability and distinctness.
    """
    logger.info(f"Generating {target_count} {subset_name} problems (Entropy: {entropy_level})...")
    
    batch_size = 500
    generated_problems = []
    attempts = 0
    max_attempts = target_count * 10  # Fail-safe against infinite loops
    
    while len(generated_problems) < target_count and attempts < max_attempts:
        attempts += 1
        batch = generate_dataset_batch(
            count=batch_size,
            entropy_level=entropy_level,
            seed=get_config().seed + attempts
        )
        
        valid_batch = []
        for prob in batch:
            # Check distinctness
            if prob.structure_hash in existing_hashes:
                continue
            
            # Check solvability (contradiction detection)
            if not is_problem_solvable(prob):
                logger.debug(f"Skipping unsolvable problem: {prob.id}")
                continue
            
            valid_batch.append(prob)
            existing_hashes.add(prob.structure_hash)
        
        generated_problems.extend(valid_batch)
        logger.debug(f"Attempt {attempts}: Generated {len(valid_batch)} valid problems. Total: {len(generated_problems)}/{target_count}")
    
    if len(generated_problems) < target_count:
        logger.warning(f"Only generated {len(generated_problems)} problems for {subset_name} after {attempts} attempts.")
    
    return generated_problems

def main():
    """Main entry point for T016."""
    parser = argparse.ArgumentParser(description="Generate and save synthetic datasets for T016")
    parser.add_argument("--high-count", type=int, default=1000, help="Number of high entropy samples")
    parser.add_argument("--low-count", type=int, default=1000, help="Number of low entropy samples")
    parser.add_argument("--target-count", type=int, default=1000, help="Number of target specific samples")
    parser.add_argument("--test-count", type=int, default=500, help="Number of test set samples")
    args = parser.parse_args()

    config = get_config()
    logger.info(f"Starting dataset generation with seed {config.seed}")

    # Ensure directories exist
    ensure_data_dir(DATA_RAW_DIR)

    # Load existing hashes to prevent overlap
    existing_hashes = load_existing_hashes()
    
    # 1. Generate High Entropy
    high_problems = generate_and_save_subset(
        "High Entropy", args.high_count, "High", existing_hashes
    )
    
    # 2. Generate Low Entropy
    low_problems = generate_and_save_subset(
        "Low Entropy", args.low_count, "Low", existing_hashes
    )
    
    # 3. Generate Target Specific
    target_problems = generate_and_save_subset(
        "Target Specific", args.target_count, "Target", existing_hashes
    )
    
    # 4. Generate Test Set (Generalization Set)
    # Must be distinct from ALL training sets
    logger.info(f"Generating {args.test_count} test set problems...")
    test_problems = generate_and_save_subset(
        "Test Set", args.test_count, "Target", existing_hashes # Using Target entropy for test, but distinct structure
    )
    
    # Save to CSVs
    logger.info("Saving datasets to CSV...")
    
    if high_problems:
        save_problems_to_csv(high_problems, FILE_HIGH, set_type="train_high")
        logger.info(f"Saved {len(high_problems)} high entropy problems to {FILE_HIGH}")
    else:
        logger.error("Failed to generate any high entropy problems.")
        sys.exit(1)

    if low_problems:
        save_problems_to_csv(low_problems, FILE_LOW, set_type="train_low")
        logger.info(f"Saved {len(low_problems)} low entropy problems to {FILE_LOW}")
    else:
        logger.error("Failed to generate any low entropy problems.")
        sys.exit(1)

    if target_problems:
        save_problems_to_csv(target_problems, FILE_TARGET, set_type="train_target")
        logger.info(f"Saved {len(target_problems)} target specific problems to {FILE_TARGET}")
    else:
        logger.error("Failed to generate any target specific problems.")
        sys.exit(1)

    if test_problems:
        save_problems_to_csv(test_problems, FILE_TEST, set_type="test_generalization")
        logger.info(f"Saved {len(test_problems)} test set problems to {FILE_TEST}")
    else:
        logger.error("Failed to generate any test set problems.")
        sys.exit(1)

    logger.info("T016 Dataset generation completed successfully.")

if __name__ == "__main__":
    main()
