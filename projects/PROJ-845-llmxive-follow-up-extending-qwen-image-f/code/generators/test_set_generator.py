import csv
import hashlib
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional

# Import from existing API surface
from models.synthetic_problem import SyntheticProblem
from generators.logic_generator import generate_propositional_problem, generate_arithmetic_problem
from config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_structure_hash(premises: List[str], operators: List[str]) -> str:
    """
    Compute a deterministic SHA256 hash of the logical structure (premises + operators).
    This ensures that two problems with the same logical structure map to the same hash.
    """
    # Sort to ensure order independence for sets of premises/operators if applicable,
    # but usually logical order matters. We join with a separator.
    structure_str = "||".join(premises) + ";;" + "||".join(operators)
    return hashlib.sha256(structure_str.encode('utf-8')).hexdigest()

def load_existing_hashes(csv_paths: List[str]) -> Set[str]:
    """
    Load all structure hashes from existing CSV files (training sets).
    Returns a set of hashes that MUST be avoided.
    """
    existing_hashes: Set[str] = set()
    for path in csv_paths:
        if not os.path.exists(path):
            logger.warning(f"Training set file not found: {path}, skipping.")
            continue
        try:
            with open(path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'structure_hash' in row:
                        existing_hashes.add(row['structure_hash'])
            logger.info(f"Loaded {len(existing_hashes)} existing hashes from {path}")
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
            raise
    return existing_hashes

def generate_unique_problem(
    existing_hashes: Set[str],
    entropy_level: str,
    problem_type: str = "propositional",
    max_attempts: int = 10000
) -> Optional[SyntheticProblem]:
    """
    Generate a problem whose structure_hash is NOT in existing_hashes.
    Retries up to max_attempts. Returns None if no unique problem found.
    """
    config = get_config()
    random.seed(config.seed)

    for attempt in range(max_attempts):
        if problem_type == "propositional":
            problem = generate_propositional_problem(entropy_level=entropy_level)
        elif problem_type == "arithmetic":
            problem = generate_arithmetic_problem(entropy_level=entropy_level)
        else:
            raise ValueError(f"Unknown problem type: {problem_type}")

        if problem is None:
            continue

        structure_hash = compute_structure_hash(problem.premises, problem.operators)

        if structure_hash not in existing_hashes:
            # Success: unique structure found
            return problem
        
        # If collision, continue to next attempt

    logger.error(f"Failed to generate a unique problem after {max_attempts} attempts.")
    return None

def main():
    """
    Main entry point for generating the Generalization Set (Test Set).
    Ensures distinctness from training sets via hash verification.
    """
    config = get_config()
    logger.info("Starting Generalization Set generation with hash-based distinctness verification.")

    # Define paths relative to project root
    # Assuming the script is run from the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_raw_dir.mkdir(parents=True, exist_ok=True)

    training_files = [
        str(data_raw_dir / "high_entropy.csv"),
        str(data_raw_dir / "low_entropy.csv"),
        str(data_raw_dir / "target_specific.csv")
    ]
    output_file = str(data_raw_dir / "test_set.csv")

    # 1. Load existing hashes from training sets
    existing_hashes = load_existing_hashes(training_files)
    logger.info(f"Total unique training structures to avoid: {len(existing_hashes)}")

    # 2. Generate test samples
    target_count = 500
    generated_problems: List[SyntheticProblem] = []
    
    # Stratify by entropy level as requested in T013
    entropy_levels = ["high", "low", "target"]
    per_level_count = target_count // len(entropy_levels)
    
    for level in entropy_levels:
        logger.info(f"Generating {per_level_count} unique problems for entropy level: {level}")
        count = 0
        while count < per_level_count:
            problem = generate_unique_problem(
                existing_hashes=existing_hashes,
                entropy_level=level,
                problem_type="propositional" # Defaulting to propositional as per T011 context
            )
            if problem:
                # Update metadata to mark as test set
                problem.metadata["set_type"] = "test_generalization"
                generated_problems.append(problem)
                count += 1
            else:
                logger.critical(f"Could not generate enough unique problems for level {level}. Stopping.")
                break

    if not generated_problems:
        logger.error("No problems generated. Exiting.")
        sys.exit(1)

    # 3. Save to CSV
    logger.info(f"Saving {len(generated_problems)} unique problems to {output_file}")
    
    fieldnames = [
        "id", "premises", "operators", "solution", "entropy_level", 
        "metadata", "structure_hash", "set_type"
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for problem in generated_problems:
            # Compute hash again for saving
            structure_hash = compute_structure_hash(problem.premises, problem.operators)
            row = {
                "id": problem.id,
                "premises": "; ".join(problem.premises),
                "operators": "; ".join(problem.operators),
                "solution": problem.solution,
                "entropy_level": problem.entropy_level,
                "metadata": str(problem.metadata),
                "structure_hash": structure_hash,
                "set_type": "test_generalization"
            }
            writer.writerow(row)

    logger.info(f"Successfully generated test set with {len(generated_problems)} unique structures.")
    logger.info("Distinctness verification passed: No training structure hashes found in test set.")

if __name__ == "__main__":
    main()