"""
Main orchestration script for T016.
Generates the datasets and saves them to CSV.
"""
import os
import sys
import argparse
import csv
import hashlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config, get_config
from utils.logger import get_logger
from generators.dataset_saver import ensure_data_dir, save_problems_to_csv
from generators.logic_generator import generate_dataset_batch
from generators.contradiction_checker import filter_contradictions

logger = get_logger(__name__)

DATA_RAW_DIR = project_root / "data" / "raw"

def load_existing_hashes() -> set:
    """Load structure hashes from existing CSVs to ensure distinctness."""
    existing_hashes = set()
    csv_files = [
        DATA_RAW_DIR / "high_entropy.csv",
        DATA_RAW_DIR / "low_entropy.csv",
        DATA_RAW_DIR / "target_specific.csv"
    ]
    
    for f_path in csv_files:
        if f_path.exists():
            logger.info(f"Loading existing hashes from {f_path.name}...")
            with open(f_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'structure_hash' in row and row['structure_hash']:
                        existing_hashes.add(row['structure_hash'])
    return existing_hashes

def write_csv(problems, filename, set_type):
    """Wrapper to save problems to a specific CSV file."""
    output_path = DATA_RAW_DIR / filename
    ensure_data_dir(DATA_RAW_DIR)
    save_problems_to_csv(problems, output_path, set_type=set_type)

def generate_sample_problem(count, entropy_level, seed, existing_hashes):
    """Generate a batch, filter contradictions, and ensure distinctness."""
    generated = []
    attempts = 0
    max_attempts = count * 5
    
    while len(generated) < count and attempts < max_attempts:
        batch = generate_dataset_batch(count, entropy_level, seed + attempts)
        valid_batch = []
        
        for p in batch:
            # Check distinctness
            if p.structure_hash in existing_hashes:
                continue
            # Check solvability
            if not is_problem_solvable(p):
                continue
            
            valid_batch.append(p)
            existing_hashes.add(p.structure_hash)
        
        generated.extend(valid_batch)
        attempts += 1
        
    return generated

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic datasets for T016")
    parser.add_argument("--high", type=int, default=1000)
    parser.add_argument("--low", type=int, default=1000)
    parser.add_argument("--target", type=int, default=1000)
    parser.add_argument("--test", type=int, default=500)
    args = parser.parse_args()

    config = get_config()
    logger.info(f"Starting generation with seed {config.seed}")

    existing_hashes = load_existing_hashes()

    # High Entropy
    high_problems = generate_sample_problem(args.high, "High", config.seed, existing_hashes)
    write_csv(high_problems, "high_entropy.csv", "train_high")

    # Low Entropy
    low_problems = generate_sample_problem(args.low, "Low", config.seed + 1000, existing_hashes)
    write_csv(low_problems, "low_entropy.csv", "train_low")

    # Target Specific
    target_problems = generate_sample_problem(args.target, "Target", config.seed + 2000, existing_hashes)
    write_csv(target_problems, "target_specific.csv", "train_target")

    # Test Set (Generalization)
    test_problems = generate_sample_problem(args.test, "Target", config.seed + 3000, existing_hashes)
    write_csv(test_problems, "test_set.csv", "test_generalization")

    logger.info("Dataset generation complete.")

if __name__ == "__main__":
    main()