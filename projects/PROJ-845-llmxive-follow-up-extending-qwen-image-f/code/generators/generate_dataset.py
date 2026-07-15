import os
import sys
import argparse
import csv
import hashlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from generators.logic_generator import generate_propositional_problem, generate_arithmetic_problem
from models.synthetic_problem import SyntheticProblem
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_sample_problem(entropy_level: str = "Medium", problem_type: str = "propositional") -> Optional[SyntheticProblem]:
    """
    Wraps the specific generators and handles the contradiction detection logic.
    Returns None if the problem is unsolvable.
    """
    if problem_type == "propositional":
        return generate_propositional_problem(entropy_level)
    elif problem_type == "arithmetic":
        return generate_arithmetic_problem(entropy_level)
    else:
        logger.error(f"Unknown problem type: {problem_type}")
        return None

def write_csv(problems: list, filepath: str):
    """
    Writes a list of SyntheticProblem objects to a CSV file.
    """
    if not problems:
        logger.warning(f"No problems to write to {filepath}")
        return

    fieldnames = ['id', 'premises', 'operators', 'solution', 'entropy_level', 'structure_hash']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for prob in problems:
            row = {
                'id': prob.id,
                'premises': ';'.join(prob.premises),
                'operators': ';'.join(prob.operators),
                'solution': prob.solution,
                'entropy_level': prob.entropy_level,
                'structure_hash': prob.metadata.get('structure_hash', '')
            }
            writer.writerow(row)
    
    logger.info(f"Wrote {len(problems)} problems to {filepath}")

def main():
    """
    Main script to generate the dataset with entropy subsets.
    """
    config = Config()
    parser = argparse.ArgumentParser(description="Generate synthetic dataset")
    parser.add_argument('--seed', type=int, default=config.seed, help="Random seed")
    parser.add_argument('--n_high', type=int, default=1000, help="Number of high entropy samples")
    parser.add_argument('--n_low', type=int, default=1000, help="Number of low entropy samples")
    parser.add_argument('--n_target', type=int, default=1000, help="Number of target specific samples")
    parser.add_argument('--output_dir', type=str, default="data/raw", help="Output directory")
    args = parser.parse_args()

    import random
    random.seed(args.seed)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Generate High Entropy
    logger.info(f"Generating {args.n_high} high entropy problems...")
    high_problems = []
    attempts = 0
    max_attempts = args.n_high * 10
    while len(high_problems) < args.n_high and attempts < max_attempts:
        p = generate_sample_problem("High")
        if p:
            high_problems.append(p)
        attempts += 1
    
    if len(high_problems) < args.n_high:
        logger.warning(f"Only generated {len(high_problems)} high entropy problems (target: {args.n_high})")

    # Generate Low Entropy
    logger.info(f"Generating {args.n_low} low entropy problems...")
    low_problems = []
    attempts = 0
    while len(low_problems) < args.n_low and attempts < max_attempts:
        p = generate_sample_problem("Low")
        if p:
            low_problems.append(p)
        attempts += 1
    
    if len(low_problems) < args.n_low:
        logger.warning(f"Only generated {len(low_problems)} low entropy problems (target: {args.n_low})")

    # Generate Target Specific
    logger.info(f"Generating {args.n_target} target specific problems...")
    target_problems = []
    attempts = 0
    while len(target_problems) < args.n_target and attempts < max_attempts:
        p = generate_sample_problem("Target")
        if p:
            target_problems.append(p)
        attempts += 1
    
    if len(target_problems) < args.n_target:
        logger.warning(f"Only generated {len(target_problems)} target specific problems (target: {args.n_target})")

    # Write CSVs
    write_csv(high_problems, os.path.join(args.output_dir, "high_entropy.csv"))
    write_csv(low_problems, os.path.join(args.output_dir, "low_entropy.csv"))
    write_csv(target_problems, os.path.join(args.output_dir, "target_specific.csv"))

    logger.info("Dataset generation complete.")

if __name__ == "__main__":
    main()
