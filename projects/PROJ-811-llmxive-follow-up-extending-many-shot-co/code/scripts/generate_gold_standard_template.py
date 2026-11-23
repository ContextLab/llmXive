"""
Script to generate a synthetic gold standard template for development testing.

This script creates `data/processed/gold_standard_annotations.json` if the human-annotated
file is missing. The template contains dummy entries with random complexity scores (1-5)
to allow development testing without blocking on human annotation.

IMPORTANT: In production, this file must be replaced by human-annotated data.
"""
import json
import os
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import random

from code.src.config import PROJECT_ROOT
from code.src.parser_utils import load_json_file, save_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path to the gold standard file
GOLD_STANDARD_PATH = PROJECT_ROOT / "data" / "processed" / "gold_standard_annotations.json"

# Number of dummy entries for the template
NUM_DUMMY_ENTRIES = 50

# Random seed for reproducibility of the template (so tests are deterministic)
RANDOM_SEED = 42

def generate_template(num_entries: int = NUM_DUMMY_ENTRIES, seed: int = RANDOM_SEED) -> Dict[str, Any]:
    """
    Generate a synthetic gold standard template with dummy entries.
    
    Args:
        num_entries: Number of dummy entries to generate.
        seed: Random seed for reproducibility.
    
    Returns:
        A dictionary representing the gold standard annotations.
    """
    random.seed(seed)
    
    template = {
        "metadata": {
            "description": "Synthetic gold standard template for development testing.",
            "note": "REPLACE WITH HUMAN-ANNOTATED DATA IN PRODUCTION.",
            "generated_at": "auto-generated",
            "num_entries": num_entries
        },
        "annotations": []
    }
    
    for i in range(num_entries):
        # Generate a dummy entry with a random complexity score (1-5)
        entry = {
            "example_id": f"dummy_{i:04d}",
            "complexity_score": random.randint(1, 5),
            "notes": "Synthetic entry for development testing only."
        }
        template["annotations"].append(entry)
    
    return template

def load_gold_standard(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load the gold standard annotations from a JSON file.
    
    Args:
        path: Path to the gold standard file. Defaults to GOLD_STANDARD_PATH.
    
    Returns:
        The loaded data as a dictionary, or None if the file does not exist.
    """
    if path is None:
        path = GOLD_STANDARD_PATH
    
    if not path.exists():
        logger.info(f"Gold standard file not found at {path}. Returning None.")
        return None
    
    try:
        data = load_json_file(path)
        return data
    except Exception as e:
        logger.error(f"Error loading gold standard file: {e}")
        return None

def save_gold_standard(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    """
    Save the gold standard annotations to a JSON file.
    
    Args:
        data: The data to save.
        path: Path to the output file. Defaults to GOLD_STANDARD_PATH.
    """
    if path is None:
        path = GOLD_STANDARD_PATH
    
    # Ensure the directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    save_json_file(data, path)
    logger.info(f"Gold standard template saved to {path}")

def main() -> None:
    """
    Main function to generate the gold standard template if it doesn't exist.
    """
    # Check if the gold standard file already exists
    if GOLD_STANDARD_PATH.exists():
        logger.info(f"Gold standard file already exists at {GOLD_STANDARD_PATH}. Skipping generation.")
        logger.info("In production, ensure this file contains human-annotated data.")
        return
    
    logger.info(f"Gold standard file not found at {GOLD_STANDARD_PATH}. Generating synthetic template.")
    
    # Generate the template
    template = generate_template()
    
    # Save the template
    save_gold_standard(template)
    
    logger.info("Synthetic gold standard template generated successfully.")
    logger.info("NOTE: This template is for development testing only. Replace with human-annotated data in production.")

if __name__ == "__main__":
    main()
