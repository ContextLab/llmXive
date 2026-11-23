import csv
import hashlib
import os
import sys
import random
import argparse
from pathlib import Path
from typing import List, Dict, Set, Any, Tuple

# Import from existing API surface
from generators.logic_generator import generate_propositional_problem, generate_arithmetic_problem
from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger
from config import get_config

logger = get_logger(__name__)

def compute_structure_hash(premises: List[str], operators: List[str]) -> str:
    """
    Computes a SHA256 hash of the logical structure (premises + operators).
    This ensures that two problems with the same logical structure but different
    variable names or specific values are considered identical for distinctness checks.
    """
    # Normalize to ensure consistent hashing regardless of list order if that matters,
    # but typically premises order defines the logic. We hash the tuple of sorted items
    # to be robust against reordering if the logic allows, or just the tuple if order matters.
    # Based on FR-008, we need to ensure structural independence.
    # We hash the string representation of the premises and operators joined.
    structure_str = "||".join(sorted(premises)) + "||" + "||".join(sorted(operators))
    return hashlib.sha256(structure_str.encode('utf-8')).hexdigest()

def load_existing_hashes(dataset_paths: List[str]) -> Set[str]:
    """
    Loads all existing structure hashes from the provided training dataset CSVs.
    This is used to ensure the test set does not overlap with training data.
    """
    existing_hashes: Set[str] = set()
    for path in dataset_paths:
        if not os.path.exists(path):
            logger.warning(f"Training dataset not found at {path}, skipping hash load.")
            continue
        
        logger.info(f"Loading structure hashes from {path}...")
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if 'structure_hash' in row:
                    existing_hashes.add(row['structure_hash'])
                    count += 1
            logger.info(f"Loaded {count} structure hashes from {path}.")
    
    return existing_hashes

def generate_distinct_problem(
    existing_hashes: Set[str], 
    max_attempts: int = 10000,
    problem_type: str = "propositional"
) -> Tuple[SyntheticProblem, str]:
    """
    Generates a problem that is guaranteed to have a structure_hash NOT present in existing_hashes.
    This implements the explicit hash-based distinctness verification required by T044.
    """
    config = get_config()
    random.seed(config.seed) # Ensure reproducibility

    for attempt in range(max_attempts):
        if problem_type == "propositional":
            problem = generate_propositional_problem()
        elif problem_type == "arithmetic":
            problem = generate_arithmetic_problem()
        else:
            raise ValueError(f"Unknown problem type: {problem_type}")

        # Compute the structure hash for this candidate
        structure_hash = compute_structure_hash(problem.premises, problem.operators)

        # Verify distinctness (The Core T044 Requirement)
        if structure_hash not in existing_hashes:
            logger.debug(f"Generated distinct problem on attempt {attempt + 1}. Hash: {structure_hash[:8]}...")
            return problem, structure_hash
        
        # If collision, loop continues to generate a new one
    
    raise RuntimeError(
        f"Failed to generate a distinct problem after {max_attempts} attempts. "
        "The training set may be too exhaustive or the generator is not diverse enough."
    )

def write_test_set_csv(
    problems: List[SyntheticProblem], 
    output_path: str,
    structure_hashes: List[str]
):
    """
    Writes the generated test set to a CSV file.
    Includes the structure_hash column to allow future verification.
    """
    ensure_data_dir(output_path)
    
    fieldnames = [
        'id', 'premises', 'operators', 'solution', 'entropy_level', 
        'structure_hash', 'metadata'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, problem in enumerate(problems):
            row = {
                'id': problem.id,
                'premises': '|'.join(problem.premises),
                'operators': '|'.join(problem.operators),
                'solution': problem.solution,
                'entropy_level': problem.entropy_level,
                'structure_hash': structure_hashes[i],
                'metadata': problem.metadata
            }
            writer.writerow(row)
    
    logger.info(f"Wrote {len(problems)} distinct test problems to {output_path}")

def ensure_data_dir(file_path: str):
    """Creates the directory for the file if it doesn't exist."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

def main():
    """
    Main entry point for generating the Generalization Set (Test Set).
    Implements T044: Explicit hash-based distinctness verification.
    """
    parser = argparse.ArgumentParser(description="Generate distinct test set for generalization.")
    parser.add_argument(
        "--training-datasets", 
        nargs='+', 
        required=True,
        help="Paths to training CSVs (high_entropy, low_entropy, target_specific) to exclude."
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Output path for test_set.csv"
    )
    parser.add_argument(
        "--num-samples", 
        type=int, 
        default=500, 
        help="Number of test samples to generate."
    )
    parser.add_argument(
        "--problem-type", 
        type=str, 
        default="propositional", 
        choices=["propositional", "arithmetic"],
        help="Type of problem to generate."
    )
    
    args = parser.parse_args()

    logger.info(f"Starting distinct test set generation for {args.num_samples} samples.")
    logger.info(f"Excluding structures from: {args.training_datasets}")

    # 1. Load existing hashes from training sets (T044 Requirement)
    existing_hashes = load_existing_hashes(args.training_datasets)
    logger.info(f"Loaded {len(existing_hashes)} unique structure hashes from training data.")

    # 2. Generate distinct problems
    problems: List[SyntheticProblem] = []
    hashes: List[str] = []

    for i in range(args.num_samples):
        try:
            problem, structure_hash = generate_distinct_problem(
                existing_hashes, 
                problem_type=args.problem_type
            )
            problems.append(problem)
            hashes.append(structure_hash)
            
            # Update existing_hashes immediately to prevent internal test set collisions
            existing_hashes.add(structure_hash)
            
        except RuntimeError as e:
            logger.error(f"Generation failed: {e}")
            sys.exit(1)

    # 3. Write to CSV
    write_test_set_csv(problems, args.output, hashes)
    logger.info("Test set generation completed successfully.")

if __name__ == "__main__":
    main()
