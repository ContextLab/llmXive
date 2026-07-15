"""
Dataset Saver for Synthetic Problems (T016).

Saves generated synthetic problems to CSV files in data/raw/ directory.
Produces: high_entropy.csv, low_entropy.csv, target_specific.csv, test_set.csv
"""
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger
from config import Config

logger = get_logger(__name__)

DATA_RAW_DIR = project_root / "data" / "raw"

def ensure_data_dir():
    """Ensure the data/raw directory exists."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured data directory exists: {DATA_RAW_DIR}")

def problem_to_row(problem: SyntheticProblem) -> Dict[str, Any]:
    """Convert a SyntheticProblem instance to a dictionary row for CSV."""
    return {
        "id": problem.id,
        "premises": "|".join(problem.premises),
        "operators": "|".join(problem.operators),
        "solution": problem.solution,
        "entropy_level": problem.entropy_level,
        "metadata": str(problem.metadata)
    }

def save_problems_to_csv(
    problems: List[SyntheticProblem],
    filename: str,
    subset_type: Optional[str] = None
) -> str:
    """
    Save a list of SyntheticProblem objects to a CSV file.
    
    Args:
        problems: List of problem instances to save.
        filename: Name of the output CSV file (saved to data/raw/).
        subset_type: Optional label for logging (e.g., "high_entropy").
    
    Returns:
        Absolute path to the saved file.
    """
    if not problems:
        logger.warning(f"No problems to save for {filename}. Skipping.")
        return str(DATA_RAW_DIR / filename)

    ensure_data_dir()
    filepath = DATA_RAW_DIR / filename
    
    # Determine columns based on SyntheticProblem fields
    fieldnames = ["id", "premises", "operators", "solution", "entropy_level", "metadata"]
    
    logger.info(f"Saving {len(problems)} problems to {filepath}...")
    
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for problem in problems:
            row = problem_to_row(problem)
            writer.writerow(row)
    
    logger.info(f"Successfully saved {len(problems)} problems to {filepath}")
    
    if subset_type:
        logger.info(f"Subset '{subset_type}' summary: {len(problems)} samples, entropy_level '{problems[0].entropy_level if problems else 'N/A'}'")
    
    return str(filepath)

def main():
    """
    Entry point for T016.
    
    This script is designed to be called by the generation pipeline.
    It expects the caller to provide the problem lists.
    For standalone testing, we simulate the data flow if no arguments are provided,
    but in the real pipeline, the generator will pass the lists here.
    """
    logger.info("Starting Dataset Saver (T016)...")
    
    # In a real pipeline, these lists would be passed from logic_generator.py
    # Since we are implementing the saver, we assume the data exists in memory 
    # or we demonstrate the capability by generating a small batch if called standalone.
    # However, per task constraints, we must produce REAL files.
    # We will attempt to import the generator to produce real data if this is run standalone.
    
    try:
        from generators.logic_generator import generate_dataset_batch
        from generators.test_set_generator import generate_unique_problem, load_existing_hashes, compute_structure_hash
        
        # Generate real data for the task
        logger.info("Generating real synthetic data for T016...")
        
        # Generate High Entropy
        high_entropy_problems = generate_dataset_batch(
            count=10, 
            entropy_level="high", 
            seed=Config().seed
        )
        save_problems_to_csv(high_entropy_problems, "high_entropy.csv", "high_entropy")
        
        # Generate Low Entropy
        low_entropy_problems = generate_dataset_batch(
            count=10, 
            entropy_level="low", 
            seed=Config().seed + 1
        )
        save_problems_to_csv(low_entropy_problems, "low_entropy.csv", "low_entropy")
        
        # Generate Target Specific
        target_problems = generate_dataset_batch(
            count=10, 
            entropy_level="target", 
            seed=Config().seed + 2
        )
        save_problems_to_csv(target_problems, "target_specific.csv", "target_specific")
        
        # Generate Test Set (Generalization)
        # We need to ensure structure_hash distinctness. 
        # We collect hashes from training sets first.
        all_training_problems = high_entropy_problems + low_entropy_problems + target_problems
        training_hashes = set()
        for p in all_training_problems:
            # Compute hash manually if not in metadata, or extract from metadata if stored
            structure = f"{''.join(p.premises)}{''.join(p.operators)}"
            h = compute_structure_hash(structure)
            training_hashes.add(h)
        
        test_problems = generate_unique_problem(
            count=5, 
            existing_hashes=training_hashes, 
            entropy_level="test"
        )
        save_problems_to_csv(test_problems, "test_set.csv", "test_set")
        
        logger.info("T016 Dataset Saver completed successfully.")
        return 0
        
    except ImportError as e:
        logger.error(f"Could not import generator modules: {e}")
        logger.error("This script expects to be run after the generator logic is available.")
        return 1
    except Exception as e:
        logger.error(f"Error during dataset saving: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
