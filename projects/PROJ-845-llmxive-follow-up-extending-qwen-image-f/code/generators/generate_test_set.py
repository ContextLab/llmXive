import os
import sys
import csv
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from generators.logic_generator import generate_propositional_problem, generate_arithmetic_problem
from models.synthetic_problem import SyntheticProblem
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_structure_hash(premises: List[str], operators: List[str]) -> str:
    """Compute SHA256 hash of premises + operators to ensure structural uniqueness."""
    content = "|".join(premises) + "||" + "|".join(operators)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def load_existing_hashes(training_paths: List[str]) -> Set[str]:
    """Load structure hashes from existing training CSVs to ensure distinctness."""
    existing_hashes = set()
    for path in training_paths:
        if not os.path.exists(path):
            logger.warning(f"Training file not found, skipping: {path}")
            continue
        
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'structure_hash' in row and row['structure_hash']:
                    existing_hashes.add(row['structure_hash'])
    
    logger.info(f"Loaded {len(existing_hashes)} existing structure hashes from training sets.")
    return existing_hashes

def generate_distinct_problem(
    existing_hashes: Set[str],
    max_attempts: int = 10000,
    entropy_level: str = "High"
) -> Tuple[SyntheticProblem, str]:
    """
    Generate a problem ensuring its structure_hash is not in existing_hashes.
    Returns (problem, hash).
    """
    for attempt in range(max_attempts):
        # Randomly choose problem type
        if random.random() < 0.5:
            problem = generate_propositional_problem()
        else:
            problem = generate_arithmetic_problem()
        
        # Ensure entropy level matches requested (override if necessary for stratification)
        problem.entropy_level = entropy_level
        
        structure_hash = compute_structure_hash(problem.premises, problem.operators)
        
        if structure_hash not in existing_hashes:
            # Add to set immediately to prevent duplicates in this run too
            existing_hashes.add(structure_hash)
            return problem, structure_hash
        
        if attempt % 1000 == 0:
            logger.debug(f"Attempt {attempt}: collision detected, retrying...")
    
    raise RuntimeError(f"Failed to generate {max_attempts} distinct problems. "
                     "The space of possible structures might be exhausted or training set too large.")

def write_test_set_csv(
    problems: List[Tuple[SyntheticProblem, str]],
    output_path: str
) -> None:
    """Write the generated test set to a CSV file."""
    # Define headers based on SyntheticProblem schema + extra fields
    fieldnames = [
        'id', 'premises', 'operators', 'solution', 'entropy_level', 
        'structure_hash', 'set_type', 'problem_type'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for problem, structure_hash in problems:
            row = {
                'id': problem.id,
                'premises': ';'.join(problem.premises),
                'operators': ';'.join(problem.operators),
                'solution': problem.solution,
                'entropy_level': problem.entropy_level,
                'structure_hash': structure_hash,
                'set_type': 'test_generalization',
                'problem_type': 'propositional' if any(k in problem.id.lower() for k in ['prop', 'logic']) else 'arithmetic'
            }
            writer.writerow(row)
    
    logger.info(f"Wrote {len(problems)} samples to {output_path}")

def main():
    """
    Main entry point to generate the Generalization Set (Test Set).
    Ensures N >= 500, distinct structure_hash from training sets, and stratification.
    """
    config = Config()
    random.seed(config.seed)
    
    # Paths
    training_files = [
        "data/raw/high_entropy.csv",
        "data/raw/low_entropy.csv",
        "data/raw/target_specific.csv"
    ]
    # Resolve to project root
    training_files = [str(project_root / f) for f in training_files]
    output_file = str(project_root / "data/raw/test_set.csv")
    
    logger.info("Starting Test Set Generation (Generalization Set)...")
    
    # 1. Load existing hashes to ensure distinctness
    existing_hashes = load_existing_hashes(training_files)
    
    # 2. Determine target counts for stratification
    # Target: N >= 500 total. Let's do ~170 per level to be safe and balanced.
    target_per_level = 170
    entropy_levels = ["High", "Low", "Target"]
    generated_problems: List[Tuple[SyntheticProblem, str]] = []
    
    for level in entropy_levels:
        logger.info(f"Generating {target_per_level} samples for {level} entropy level...")
        count = 0
        while count < target_per_level:
            try:
                problem, structure_hash = generate_distinct_problem(
                    existing_hashes, 
                    entropy_level=level
                )
                generated_problems.append((problem, structure_hash))
                count += 1
            except RuntimeError as e:
                logger.error(f"Generation failed for {level}: {e}")
                sys.exit(1)
        
        logger.info(f"Completed {level} level: {count} samples.")
    
    # 3. Write to CSV
    write_test_set_csv(generated_problems, output_file)
    
    # 4. Verification
    if len(generated_problems) < 500:
        logger.error(f"Verification Failed: Generated {len(generated_problems)} samples, required >= 500.")
        sys.exit(1)
    
    logger.info(f"Success: Generated {len(generated_problems)} distinct test samples.")
    logger.info(f"Output written to: {output_file}")

if __name__ == "__main__":
    main()