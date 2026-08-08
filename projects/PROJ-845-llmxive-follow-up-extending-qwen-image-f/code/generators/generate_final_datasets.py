"""
T016 Implementation: Save generated CSVs to data/raw/

This script orchestrates the generation and saving of the four required CSV files:
- data/raw/high_entropy.csv
- data/raw/low_entropy.csv
- data/raw/target_specific.csv
- data/raw/test_set.csv

It utilizes the existing generator modules to produce the data and the dataset_saver
module to persist it in the correct format.
"""
import os
import sys
import argparse
import csv
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root is the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Ensure we can import sibling modules
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config, get_config
from utils.logger import get_logger
from models.synthetic_problem import SyntheticProblem
from generators.logic_generator import generate_dataset_batch
from generators.test_set_generator import generate_unique_problem, compute_structure_hash, load_existing_hashes, write_test_set_csv
from generators.dataset_saver import save_problems_to_csv, ensure_data_dir

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Generate and save final synthetic datasets (T016)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--n_train", type=int, default=1000, help="Number of samples per training subset")
    parser.add_argument("--n_test", type=int, default=500, help="Number of samples for test set")
    parser.add_argument("--entropy_level", type=str, default="high", choices=["high", "low", "target"],
                        help="Target entropy level for specific generation (optional override)")
    args = parser.parse_args()

    # Initialize Config with seed
    config = get_config()
    random.seed(args.seed)
    
    logger.info(f"Starting dataset generation with seed={args.seed}")
    logger.info(f"Target sizes: Train={args.n_train} per subset, Test={args.n_test}")

    # Ensure output directory exists
    ensure_data_dir(DATA_RAW_DIR)

    # ------------------------------------------------------------------
    # 1. Generate Training Subsets (High, Low, Target)
    # ------------------------------------------------------------------
    # We use the existing generate_dataset_batch which handles entropy parameterization
    # based on T012 implementation.
    
    training_configs = [
        ("high_entropy", "high", args.n_train),
        ("low_entropy", "low", args.n_train),
        ("target_specific", "target", args.n_train)
    ]

    all_training_problems: List[SyntheticProblem] = []

    for filename, entropy_mode, count in training_configs:
        logger.info(f"Generating {count} problems for {filename} (entropy={entropy_mode})")
        
        # Generate batch
        problems = generate_dataset_batch(
            count=count,
            entropy_mode=entropy_mode,
            seed=args.seed + hash(filename) % 1000  # Offset seed for variety but reproducible
        )
        
        # Filter contradictions if needed (T014 logic)
        # Assuming generate_dataset_batch already filters or we do it here if needed.
        # For T016, we assume the generator produces valid problems.
        
        # Save to CSV
        output_path = DATA_RAW_DIR / filename
        save_problems_to_csv(problems, output_path)
        
        all_training_problems.extend(problems)
        logger.info(f"Saved {len(problems)} problems to {output_path}")

    # ------------------------------------------------------------------
    # 2. Generate Generalization Test Set (Distinct from Training)
    # ------------------------------------------------------------------
    # T013 requirement: structure_hash must NOT be present in any training subset.
    # T016 requirement: Save to data/raw/test_set.csv with all fields.
    
    logger.info("Generating distinct test set...")
    
    # Load existing hashes from training data to ensure distinctness
    existing_hashes = load_existing_hashes(all_training_problems)
    
    test_problems = []
    attempts = 0
    max_attempts = args.n_test * 10  # Prevent infinite loops if distinctness is hard
    
    while len(test_problems) < args.n_test and attempts < max_attempts:
        attempts += 1
        # Generate a unique problem
        prob = generate_unique_problem(
            existing_hashes=existing_hashes,
            seed=args.seed + attempts
        )
        
        # Double check hash uniqueness (defensive)
        if prob.structure_hash not in existing_hashes:
            test_problems.append(prob)
            existing_hashes.add(prob.structure_hash)
        else:
            logger.debug(f"Attempt {attempts} produced duplicate hash, skipping.")

    if len(test_problems) < args.n_test:
        logger.error(f"Failed to generate {args.n_test} distinct test problems after {max_attempts} attempts.")
        sys.exit(1)

    # Save test set
    test_output_path = DATA_RAW_DIR / "test_set.csv"
    save_problems_to_csv(test_problems, test_output_path)
    logger.info(f"Saved {len(test_problems)} distinct test problems to {test_output_path}")

    logger.info("T016: All datasets generated and saved successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
