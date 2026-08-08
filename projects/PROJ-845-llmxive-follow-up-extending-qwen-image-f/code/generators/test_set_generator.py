"""
Test Set Generator for Generalization Set (T013).

Generates a distinct Generalization Set (data/raw/test_set.csv) with N_test >= 500,
ensuring each sample's structure_hash (SHA256 of premises + operators) is NOT present
in any training subset. Stratifies by entropy level.
"""
import csv
import hashlib
import os
import sys
import random
import argparse
from pathlib import Path
from typing import List, Dict, Set, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.synthetic_problem import SyntheticProblem
from generators.logic_generator import generate_propositional_problem, generate_arithmetic_problem
from config import Config, get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_structure_hash(premises: List[str], operators: List[str]) -> str:
    """Compute SHA256 hash of premises + operators to identify structural distinctness."""
    content = " ".join(premises) + " " + " ".join(operators)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def load_existing_hashes(training_paths: List[str]) -> Set[str]:
    """Load all structure_hash values from existing training CSVs."""
    existing_hashes: Set[str] = set()
    for path_str in training_paths:
        path = Path(path_str)
        if not path.exists():
            logger.warning(f"Training path does not exist: {path}, skipping.")
            continue
        
        logger.info(f"Loading hashes from {path}...")
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if 'structure_hash' in row:
                    existing_hashes.add(row['structure_hash'])
                    count += 1
        logger.info(f"Loaded {count} hashes from {path.name}.")
    
    return existing_hashes

def generate_unique_problem(
    existing_hashes: Set[str],
    target_entropy: Optional[str] = None,
    max_attempts: int = 10000
) -> Optional[SyntheticProblem]:
    """
    Generate a problem whose structure_hash is NOT in existing_hashes.
    If target_entropy is provided, attempts to match it (best effort).
    """
    for attempt in range(max_attempts):
        # Randomly choose problem type
        if random.random() < 0.5:
            prob = generate_propositional_problem()
        else:
            prob = generate_arithmetic_problem()
        
        # Compute hash
        structure_hash = compute_structure_hash(prob.premises, prob.operators)
        
        if structure_hash not in existing_hashes:
            # Update metadata to reflect entropy level if needed
            if target_entropy:
                prob.metadata['target_entropy'] = target_entropy
            prob.metadata['generation_attempt'] = attempt
            return prob
        
        if attempt % 1000 == 0:
            logger.debug(f"Attempt {attempt}: Hash collision, retrying...")
    
    logger.error(f"Failed to generate unique problem after {max_attempts} attempts.")
    return None

def write_test_set_csv(
    problems: List[SyntheticProblem],
    output_path: str,
    entropy_levels: List[str]
) -> None:
    """Write the generated problems to CSV with stratification metadata."""
    ensure_data_dir(output_path)
    
    fieldnames = [
        'id', 'premises', 'operators', 'solution', 'entropy_level', 
        'structure_hash', 'set_type', 'metadata'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, prob in enumerate(problems):
            # Determine entropy level (use metadata if set, else default)
            ent_level = prob.metadata.get('entropy_level', 'unknown')
            if target_entropy := prob.metadata.get('target_entropy'):
                ent_level = target_entropy
            
            row = {
                'id': prob.id,
                'premises': ';'.join(prob.premises),
                'operators': ';'.join(prob.operators),
                'solution': prob.solution,
                'entropy_level': ent_level,
                'structure_hash': compute_structure_hash(prob.premises, prob.operators),
                'set_type': 'test_generalization',
                'metadata': str(prob.metadata)
            }
            writer.writerow(row)
    
    logger.info(f"Wrote {len(problems)} problems to {output_path}")

def ensure_data_dir(file_path: str) -> None:
    """Ensure the directory for the given file path exists."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """
    Main entry point for generating the Generalization Set (T013).
    
    Usage:
      python code/generators/test_set_generator.py --output data/raw/test_set.csv \
        --training data/raw/high_entropy.csv data/raw/low_entropy.csv data/raw/target_specific.csv \
        --n_test 500
    """
    parser = argparse.ArgumentParser(description="Generate distinct Generalization Set.")
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/raw/test_set.csv',
        help='Output path for test set CSV'
    )
    parser.add_argument(
        '--training', 
        nargs='+', 
        default=[
            'data/raw/high_entropy.csv',
            'data/raw/low_entropy.csv',
            'data/raw/target_specific.csv'
        ],
        help='Paths to training CSVs to exclude hashes from'
    )
    parser.add_argument(
        '--n_test', 
        type=int, 
        default=500,
        help='Number of test samples to generate (default: 500)'
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        default=None,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    if args.seed is not None:
        random.seed(args.seed)
        config = get_config()
        config.seed = args.seed
    
    logger.info(f"Starting test set generation: N={args.n_test}")
    
    # Load existing hashes from training sets
    existing_hashes = load_existing_hashes(args.training)
    logger.info(f"Loaded {len(existing_hashes)} existing structure hashes.")
    
    # Define stratification targets
    # Stratify by entropy level: High, Low, Target (approx equal split)
    entropy_levels = ['High', 'Low', 'Target']
    samples_per_level = args.n_test // len(entropy_levels)
    remainder = args.n_test % len(entropy_levels)
    
    all_problems: List[SyntheticProblem] = []
    
    for i, level in enumerate(entropy_levels):
        count = samples_per_level + (1 if i < remainder else 0)
        logger.info(f"Generating {count} problems for entropy level: {level}")
        
        generated = 0
        attempts = 0
        max_total_attempts = count * 10000
        
        while generated < count and attempts < max_total_attempts:
            prob = generate_unique_problem(
                existing_hashes, 
                target_entropy=level,
                max_attempts=1000
            )
            if prob:
                # Add to existing_hashes to prevent duplicates within test set too
                h = compute_structure_hash(prob.premises, prob.operators)
                existing_hashes.add(h)
                all_problems.append(prob)
                generated += 1
            attempts += 1
        
        if generated < count:
            logger.warning(f"Could only generate {generated}/{count} for level {level}")
    
    if len(all_problems) < 500:
        logger.error(f"Generated only {len(all_problems)} test samples, requirement is >= 500.")
        sys.exit(1)
    
    write_test_set_csv(all_problems, args.output, entropy_levels)
    logger.info(f"Successfully generated {len(all_problems)} distinct test samples.")

if __name__ == '__main__':
    main()
