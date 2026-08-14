import os
import sys
import random
import csv
import json
from pathlib import Path
import logging
from typing import List, Dict, Any

# Add parent directory to path to allow imports from utils if needed,
# though this script primarily uses standard library and local data files.
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

def setup_output_directories():
    """Ensure the ground_truth directory exists."""
    ground_truth_dir = Path("data/ground_truth")
    ground_truth_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {ground_truth_dir}")
    return ground_truth_dir

def load_matched_pairs(csv_path: str = "data/processed/matched_pairs.csv") -> List[Dict[str, Any]]:
    """
    Load the matched pairs CSV.
    Expected columns include at least: block_id, repo_id, label (LLM/Human), and potentially others.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Matched pairs file not found: {csv_path}")
    
    rows = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    logger.info(f"Loaded {len(rows)} matched pairs from {csv_path}")
    return rows

def select_ground_truth_blocks(
    pairs: List[Dict[str, Any]], 
    min_count: int = 10, 
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Randomly select at least min_count blocks for manual verification.
    
    Logic:
    1. Shuffle the list of all available blocks.
    2. Select the first min_count (or all if fewer exist).
    3. Ensure stratification if possible (though simple random is requested).
       We will do a simple random sample as per task description "randomly select".
    """
    if not pairs:
        raise ValueError("No matched pairs found to select ground truth from.")
    
    random.seed(seed)
    shuffled = pairs.copy()
    random.shuffle(shuffled)
    
    selected = shuffled[:min_count]
    
    # If we have fewer than min_count, we take all available (and log a warning)
    if len(selected) < min_count:
        logger.warning(f"Only {len(selected)} blocks available, selecting all for ground truth.")
    
    logger.info(f"Selected {len(selected)} blocks for ground truth verification.")
    return selected

def save_ground_truth(
    blocks: List[Dict[str, Any]], 
    output_path: str = "data/ground_truth/manual_labels.csv"
):
    """
    Save the selected blocks to the ground truth CSV.
    The file will contain the original columns plus a 'selected_for_ground_truth' flag (set to True)
    and potentially a 'manual_label' column (initially empty or 'pending').
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not blocks:
        logger.warning("No blocks to save for ground truth.")
        # Create an empty file with headers if possible, or just return.
        # We'll write headers based on the first block if available, else generic.
        headers = ["block_id", "repo_id", "label", "manual_label", "selected_for_ground_truth"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return

    # Determine headers: use existing keys + manual_label + selected flag
    # We want to preserve original data but ensure manual_label exists.
    base_keys = list(blocks[0].keys())
    if "manual_label" not in base_keys:
        base_keys.append("manual_label")
    if "selected_for_ground_truth" not in base_keys:
        base_keys.append("selected_for_ground_truth")
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=base_keys)
        writer.writeheader()
        
        for block in blocks:
            row = block.copy()
            # Ensure manual_label is present (empty string for now)
            row["manual_label"] = row.get("manual_label", "")
            row["selected_for_ground_truth"] = True
            writer.writerow(row)
    
    logger.info(f"Saved {len(blocks)} ground truth blocks to {output_path}")

def main():
    """
    Main entry point for ground truth selection.
    1. Load matched pairs.
    2. Randomly select >= 10 blocks.
    3. Save to data/ground_truth/manual_labels.csv.
    """
    setup_logging()
    setup_output_directories()
    
    try:
        pairs = load_matched_pairs()
        
        if not pairs:
            logger.error("No matched pairs found. Cannot select ground truth.")
            sys.exit(1)
        
        selected_blocks = select_ground_truth_blocks(pairs, min_count=10)
        
        output_path = "data/ground_truth/manual_labels.csv"
        save_ground_truth(selected_blocks, output_path)
        
        logger.info("Ground truth selection completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during ground truth selection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
