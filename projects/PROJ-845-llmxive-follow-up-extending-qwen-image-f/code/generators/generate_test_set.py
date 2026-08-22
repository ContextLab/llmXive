"""
Task T013: Implement generation of a distinct Generalization Set (test_set.csv).

This script generates a test set with N >= 500 samples.
It ensures that the structure_hash of every test sample is NOT present in any
training subset (high_entropy, low_entropy, target_specific).
It also stratifies the test set by entropy level.
"""
import os
import sys
import csv
import hashlib
import random
import argparse
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.synthetic_problem import SyntheticProblem
from generators.logic_generator import generate_propositional_problem, generate_arithmetic_problem
from generators.contradiction_checker import is_problem_solvable
from utils.logger import get_logger
from config import get_config

logger = get_logger(__name__)
config = get_config()

def compute_structure_hash(premises: List[str], operators: List[str]) -> str:
    """
    Compute a SHA256 hash of the logical structure (premises + operators).
    This ensures semantically identical structures are identified as the same,
    regardless of minor syntactic variations (if canonicalized).
    """
    # Sort to ensure order independence if the structure allows, 
    # but typically premises order matters in logic. 
    # Based on T050, we use a canonical string representation.
    # Here we join premises and operators with a delimiter.
    structure_str = "|||".join(premises) + ":::" + "|||".join(operators)
    return hashlib.sha256(structure_str.encode('utf-8')).hexdigest()

def load_existing_hashes(data_dir: str) -> Set[str]:
    """
    Load all structure hashes from existing training CSVs to ensure distinctness.
    """
    existing_hashes: Set[str] = set()
    training_files = [
        "high_entropy.csv",
        "low_entropy.csv",
        "target_specific.csv"
    ]
    
    for filename in training_files:
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Training file not found, skipping: {filepath}")
            continue
        
        logger.info(f"Loading hashes from {filepath}...")
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                if 'structure_hash' in row:
                    existing_hashes.add(row['structure_hash'])
                    count += 1
            logger.info(f"Loaded {count} hashes from {filename}")
    
    return existing_hashes

def generate_distinct_problem(
    existing_hashes: Set[str],
    target_entropy_level: str,
    max_attempts: int = 10000
) -> Optional[SyntheticProblem]:
    """
    Generate a problem that is solvable and has a structure_hash not in existing_hashes.
    """
    for attempt in range(max_attempts):
        # Determine problem type based on entropy level to ensure diversity
        if target_entropy_level == "high":
            # More complex, randomized logic
            prob = random.random()
            if prob > 0.5:
                problem = generate_propositional_problem(complexity="high")
            else:
                problem = generate_arithmetic_problem(complexity="high")
        elif target_entropy_level == "low":
            # Simple, repetitive logic
            prob = random.random()
            if prob > 0.5:
                problem = generate_propositional_problem(complexity="low")
            else:
                problem = generate_arithmetic_problem(complexity="low")
        else: # target
            # Specific reasoning style
            problem = generate_propositional_problem(complexity="medium")
        
        if not problem:
            continue

        # Check solvability (contradiction check)
        if not is_problem_solvable(problem.premises, problem.operators):
            continue

        # Compute structure hash
        structure_hash = compute_structure_hash(problem.premises, problem.operators)

        # Check distinctness
        if structure_hash in existing_hashes:
            continue

        # Found a valid distinct problem
        # Update metadata
        if problem.metadata is None:
            problem.metadata = {}
        problem.metadata['generation_attempt'] = attempt + 1
        problem.metadata['entropy_level'] = target_entropy_level
        
        return problem

    logger.error(f"Failed to generate distinct problem for {target_entropy_level} after {max_attempts} attempts")
    return None

def write_test_set_csv(
    problems: List[SyntheticProblem],
    output_path: str
) -> None:
    """
    Write the list of problems to a CSV file.
    """
    if not problems:
        logger.error("No problems to write.")
        return

    fieldnames = [
        'id', 'premises', 'operators', 'solution', 
        'entropy_level', 'structure_hash', 'set_type', 'metadata'
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for p in problems:
            row = {
                'id': p.id,
                'premises': ';'.join(p.premises),
                'operators': ';'.join(p.operators),
                'solution': p.solution,
                'entropy_level': p.entropy_level,
                'structure_hash': compute_structure_hash(p.premises, p.operators),
                'set_type': 'test_generalization',
                'metadata': json.dumps(p.metadata) if p.metadata else '{}'
            }
            writer.writerow(row)

    logger.info(f"Wrote {len(problems)} problems to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate distinct Generalization Set (Test Set)")
    parser.add_argument('--input-dir', type=str, default='data/raw',
                        help='Directory containing training CSVs to exclude hashes from')
    parser.add_argument('--output-file', type=str, default='data/raw/test_set.csv',
                        help='Path to write the test set CSV')
    parser.add_argument('--count', type=int, default=500,
                        help='Number of test samples to generate')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        config.seed = args.seed

    input_dir = args.input_dir
    output_path = args.output_file
    target_count = args.count

    logger.info(f"Loading existing structure hashes from {input_dir}...")
    existing_hashes = load_existing_hashes(input_dir)
    logger.info(f"Total existing hashes to avoid: {len(existing_hashes)}")

    # Stratification: We want a mix of entropy levels in the test set
    # Let's aim for roughly equal distribution or proportional to training
    # For now, let's do a balanced stratification: High, Low, Target
    stratification_counts = {
        "high": target_count // 3,
        "low": target_count // 3,
        "target": target_count - (target_count // 3) * 2
    }

    all_problems: List[SyntheticProblem] = []
    
    for entropy_level, count in stratification_counts.items():
        logger.info(f"Generating {count} distinct problems for entropy level: {entropy_level}")
        count_generated = 0
        while count_generated < count:
            problem = generate_distinct_problem(
                existing_hashes=existing_hashes,
                target_entropy_level=entropy_level,
                max_attempts=5000 # Limit attempts per problem to avoid infinite loops
            )
            
            if problem:
                # Update the hash in the problem metadata or just recompute on write
                # We rely on write_test_set_csv to compute the hash for the row
                all_problems.append(problem)
                count_generated += 1
                existing_hashes.add(compute_structure_hash(problem.premises, problem.operators))
            else:
                logger.critical(f"Could not generate enough distinct problems for {entropy_level}. Stopping.")
                break
        
        logger.info(f"Completed {entropy_level}: generated {count_generated}/{count}")

    if len(all_problems) < target_count:
        logger.warning(f"Only generated {len(all_problems)} problems, requested {target_count}.")
    
    logger.info(f"Writing test set to {output_path}...")
    write_test_set_csv(all_problems, output_path)

    logger.info("T013 Test Set Generation Complete.")

if __name__ == "__main__":
    main()
