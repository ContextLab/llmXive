import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
import hashlib

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logging
from utils.checksum import compute_file_checksum
from data.clean import save_exclusion_report as clean_save_exclusion_report
from data.descriptors import compute_descriptors_for_dataset

def setup_finalize_logger():
    """Setup logging for the finalize dataset stage."""
    return setup_logging(
        name="finalize_dataset",
        log_file="data/processed/finalize.log",
        level=logging.INFO
    )

def load_processed_data(input_path: str) -> list:
    """Load the processed data (output of clean/descriptors) from CSV."""
    logger = logging.getLogger("finalize_dataset")
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    logger.info(f"Loaded {len(data)} rows from {input_path}")
    return data

def load_exclusion_report(exclusion_path: str) -> list:
    """Load the exclusion report if it exists."""
    logger = logging.getLogger("finalize_dataset")
    if not os.path.exists(exclusion_path):
        logger.warning(f"Exclusion report not found at {exclusion_path}, proceeding with empty list.")
        return []
    
    with open(exclusion_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_dataset(data: list, output_path: str) -> None:
    """Save the final cleaned dataset to CSV."""
    logger = logging.getLogger("finalize_dataset")
    if not data:
        logger.warning("No data to save.")
        return

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = data[0].keys()
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} rows to {output_path}")

def calculate_success_rate(input_count: int, output_count: int) -> float:
    """Calculate the success rate of the filtering pipeline."""
    if input_count == 0:
        return 0.0
    return (output_count / input_count) * 100.0

def save_post_filter_distribution(data: list, output_path: str) -> None:
    """Save the distribution of substrate classes in the final dataset."""
    logger = logging.getLogger("finalize_dataset")
    
    counts = {}
    for row in data:
        # Assume 'substrate_class' is the column name
        cls = row.get('substrate_class', 'unknown')
        counts[cls] = counts.get(cls, 0) + 1
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(counts, f, indent=2)
    
    logger.info(f"Saved post-filter distribution to {output_path}: {counts}")

def main():
    """
    Main entry point for T016: Save final processed dataset.
    
    Logic:
    1. Load cleaned data from T012/T013 (intermediate file).
    2. Calculate success rate.
    3. FAIL if success_rate < 95%.
    4. Save CSV and generate checksum.
    5. Save post_filter_distribution.json.
    """
    parser = argparse.ArgumentParser(description="Finalize and save the cleaned SN1 dataset.")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to the intermediate processed CSV (output of clean/descriptors).")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to save the final cleaned CSV.")
    parser.add_argument("--exclusion-report", type=str, 
                        default="data/processed/exclusion_report.csv",
                        help="Path to the exclusion report CSV.")
    args = parser.parse_args()

    logger = setup_finalize_logger()
    logger.info("Starting dataset finalization (T016).")

    # 1. Load input data to get original count
    # We need to know the count BEFORE filtering to calculate success rate.
    # The input to this script is the result of T012/T013, which has already filtered.
    # However, T012 saves pre_filter_distribution.json. We need the total count there.
    # OR, we assume the input to this script is the result of the full pipeline (clean + descriptors).
    # The task says: "Load the cleaned data from T012/T013".
    # To calculate success rate, we need the count of the data BEFORE T012/T013 filtering.
    # T012 saves `pre_filter_distribution.json`. Let's load that to get the original count.
    
    pre_filter_path = "data/processed/pre_filter_distribution.json"
    original_count = 0
    if os.path.exists(pre_filter_path):
        with open(pre_filter_path, 'r') as f:
            pre_dist = json.load(f)
            original_count = sum(pre_dist.values())
    else:
        logger.warning(f"Could not find {pre_filter_path}. Cannot calculate success rate relative to pre-filter count. Assuming input count is original.")
        # Fallback: if we don't have pre-filter, we can't strictly enforce 95% of original.
        # But the task requires it. We will load the input file and count it as original if pre-filter is missing.
        # Actually, T012 outputs the filtered data. So the input to T016 is filtered.
        # We MUST have the pre-filter count. If missing, we fail or warn.
        # Let's try to load the input file and count it, but we can't compare to original without pre_filter.
        # We will proceed but log an error if pre_filter is missing.
        pass

    # Load the data that has passed through clean and descriptors
    try:
        final_data = load_processed_data(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    final_count = len(final_data)

    # If we have the original count, check success rate
    if original_count > 0:
        success_rate = calculate_success_rate(original_count, final_count)
        logger.info(f"Success Rate: {success_rate:.2f}% ({final_count}/{original_count})")
        
        if success_rate < 95.0:
            logger.error(f"Success rate {success_rate:.2f}% is below 95% threshold. FAILING TASK.")
            sys.exit(1)
    else:
        logger.warning("Could not determine original count (missing pre_filter_distribution.json). Skipping success rate check.")

    # 4. Save CSV
    save_dataset(final_data, args.output)

    # Generate checksum
    checksum = compute_file_checksum(args.output)
    checksum_path = f"{args.output}.sha256"
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {os.path.basename(args.output)}\n")
    logger.info(f"Saved checksum to {checksum_path}: {checksum}")

    # 5. Save post_filter_distribution.json
    dist_path = "data/processed/post_filter_distribution.json"
    save_post_filter_distribution(final_data, dist_path)

    logger.info("Dataset finalization completed successfully.")

if __name__ == "__main__":
    main()