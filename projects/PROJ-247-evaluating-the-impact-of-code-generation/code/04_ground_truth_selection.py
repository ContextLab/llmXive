"""
T017a: Ground Truth Selection Script

Randomly selects at least 10 code blocks from the matched pairs dataset
for manual verification and saves them to data/ground_truth/manual_labels.csv.

This script assumes that `data/processed/matched_pairs.csv` has been generated
by the previous tasks (T015).
"""

import os
import sys
import random
import csv
import json
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, setup_logging

# Constants
MIN_SELECTION_COUNT = 10
INPUT_FILE = project_root / "data" / "processed" / "matched_pairs.csv"
OUTPUT_FILE = project_root / "data" / "ground_truth" / "manual_labels.csv"
LOG_FILE = project_root / "data" / "logs" / "ground_truth_selection.log"

def setup_output_directories():
    """Ensure the output directory exists."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured output directory exists: {OUTPUT_FILE.parent}")

def load_matched_pairs():
    """
    Load the matched pairs from the CSV file.
    Returns a list of dictionaries.
    """
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}. "
                                "Please run T015 (matching) first.")

    blocks = []
    with open(INPUT_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure we have the necessary fields for the ground truth file
            # Expected fields based on typical pipeline output:
            # repo_id, block_id, label, confidence, complexity, etc.
            blocks.append(row)
    
    logging.info(f"Loaded {len(blocks)} blocks from {INPUT_FILE}")
    return blocks

def select_ground_truth_blocks(blocks, count=MIN_SELECTION_COUNT):
    """
    Randomly select a subset of blocks for manual verification.
    """
    if len(blocks) < count:
        logging.warning(f"Only {len(blocks)} blocks available, selecting all.")
        count = len(blocks)
    
    selected = random.sample(blocks, count)
    logging.info(f"Randomly selected {len(selected)} blocks for ground truth.")
    return selected

def save_ground_truth(selected_blocks, output_path):
    """
    Save the selected blocks to the ground truth CSV file.
    Adds metadata columns for the manual labeling process.
    """
    fieldnames = list(selected_blocks[0].keys()) + [
        "manual_label",
        "manual_confidence",
        "reviewer_id",
        "review_date"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for block in selected_blocks:
            # Initialize manual fields as empty
            row = dict(block)
            row["manual_label"] = ""
            row["manual_confidence"] = ""
            row["reviewer_id"] = ""
            row["review_date"] = ""
            writer.writerow(row)

    logging.info(f"Saved {len(selected_blocks)} blocks to {output_path}")

def main():
    """Main entry point for the ground truth selection task."""
    # Setup logging
    setup_logging(log_file=str(LOG_FILE))
    logger = get_logger(__name__)
    logger.info("Starting Ground Truth Selection (T017a)")

    try:
        setup_output_directories()
        
        # Load data
        blocks = load_matched_pairs()
        
        if not blocks:
            logger.error("No blocks found in matched pairs. Cannot select ground truth.")
            return 1

        # Select blocks
        selected = select_ground_truth_blocks(blocks, MIN_SELECTION_COUNT)
        
        # Save output
        save_ground_truth(selected, OUTPUT_FILE)
        
        logger.info("Ground Truth Selection completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during ground truth selection: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
