"""
Dataset Saver Module for T016.
Handles conversion of SyntheticProblem objects to CSV rows and file writing.
"""
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger

logger = get_logger(__name__)

def ensure_data_dir(dir_path: Path) -> None:
    """Ensure the data directory exists."""
    if not dir_path.exists():
        logger.info(f"Creating data directory: {dir_path}")
        dir_path.mkdir(parents=True, exist_ok=True)

def problem_to_row(problem: SyntheticProblem, set_type: str = "train") -> Dict[str, Any]:
    """
    Convert a SyntheticProblem object to a dictionary row for CSV.
    Ensures all required columns are present.
    """
    # Serialize premises and operators lists to JSON strings for CSV storage
    premises_str = json.dumps(problem.premises)
    operators_str = json.dumps(problem.operators)
    metadata_str = json.dumps(problem.metadata)

    return {
        "id": problem.id,
        "premises": premises_str,
        "operators": operators_str,
        "solution": problem.solution,
        "entropy_level": problem.entropy_level,
        "structure_hash": problem.structure_hash,
        "set_type": set_type,
        "metadata": metadata_str
    }

def save_problems_to_csv(
    problems: List[SyntheticProblem], 
    output_path: Path, 
    set_type: str = "train"
) -> None:
    """
    Save a list of SyntheticProblem objects to a CSV file.
    Columns match the SyntheticProblem schema plus set_type.
    """
    if not problems:
        logger.warning(f"No problems to save to {output_path}")
        return

    # Define fieldnames explicitly
    fieldnames = [
        "id", "premises", "operators", "solution", "entropy_level", 
        "structure_hash", "set_type", "metadata"
    ]

    rows = [problem_to_row(p, set_type) for p in problems]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Successfully wrote {len(problems)} rows to {output_path}")

def main():
    """
    Main entry point for testing the saver module directly.
    """
    # This is primarily a module for use by generate_datasets.py
    pass
