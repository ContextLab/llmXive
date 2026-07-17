import os
import sys
import random
import csv
import json
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path to allow imports of utils
# Assuming this script is run from the project root or code directory
# We handle relative imports dynamically if needed, but standard practice is absolute or relative to root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import get_logger

logger = get_logger(__name__)

def setup_output_directories():
    """Ensure the ground truth directory exists."""
    output_dir = PROJECT_ROOT / "data" / "ground_truth"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")
    return output_dir

def load_matched_pairs():
    """
    Load the matched pairs from the processed data.
    Expected file: data/processed/matched_pairs.csv
    """
    input_file = PROJECT_ROOT / "data" / "processed" / "matched_pairs.csv"
    if not input_file.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_file}. "
            "Please ensure T015 (matching) has been completed successfully."
        )

    pairs = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append(row)
    
    logger.info(f"Loaded {len(pairs)} matched pairs from {input_file}")
    return pairs

def select_ground_truth_blocks(pairs: List[Dict[str, Any]], sample_size: int = 10) -> List[Dict[str, Any]]:
    """
    Randomly select a subset of blocks for manual verification.
    
    Args:
        pairs: List of matched pair dictionaries.
        sample_size: Minimum number of blocks to select (default 10).
    
    Returns:
        List of selected block dictionaries.
    """
    if len(pairs) == 0:
        raise ValueError("No matched pairs found to sample from.")
    
    # Ensure we don't sample more than available
    actual_size = min(sample_size, len(pairs))
    
    # Random selection without replacement
    selected = random.sample(pairs, actual_size)
    
    logger.info(f"Randomly selected {actual_size} blocks for ground truth verification.")
    return selected

def save_ground_truth(selected_blocks: List[Dict[str, Any]], output_dir: Path):
    """
    Save the selected blocks to the manual_labels.csv file.
    
    The file will contain the block data with an additional column 
    'manual_label' initialized to empty, indicating it needs manual verification.
    
    Output: data/ground_truth/manual_labels.csv
    """
    output_file = output_dir / "manual_labels.csv"
    
    if not selected_blocks:
        logger.warning("No blocks selected to save.")
        return

    # Determine fieldnames from the first block, ensuring 'manual_label' is included
    if selected_blocks:
        fieldnames = list(selected_blocks[0].keys())
        if 'manual_label' not in fieldnames:
            fieldnames.append('manual_label')
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for block in selected_blocks:
            # Ensure manual_label key exists, default to empty string
            record = dict(block)
            record['manual_label'] = ''
            writer.writerow(record)
    
    logger.info(f"Saved {len(selected_blocks)} blocks to {output_file}")

def main():
    """Main entry point for ground truth selection."""
    logger.info("Starting Ground Truth Selection (T017a)...")
    
    try:
        # 1. Setup directories
        output_dir = setup_output_directories()
        
        # 2. Load matched pairs
        pairs = load_matched_pairs()
        
        # 3. Select random blocks (minimum 10)
        selected_blocks = select_ground_truth_blocks(pairs, sample_size=10)
        
        # 4. Save to CSV
        save_ground_truth(selected_blocks, output_dir)
        
        logger.info("Ground Truth Selection completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Selection error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during ground truth selection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()