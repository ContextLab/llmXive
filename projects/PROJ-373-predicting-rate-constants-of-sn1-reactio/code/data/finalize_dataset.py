"""
Finalize the dataset by merging cleaned data and exclusion reports.
Computes success rates and checksums.
"""
import os
import sys
import csv
import json
import logging
import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

def setup_finalize_logger(log_file: Path):
    """Setup logging for the finalize stage."""
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return get_logger(__name__)

def load_processed_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load the cleaned intermediate data."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def load_exclusion_report(exclusion_path: Path) -> List[Dict[str, Any]]:
    """Load the exclusion report."""
    if not exclusion_path.exists():
        raise FileNotFoundError(f"Exclusion report not found: {exclusion_path}")
    
    data = []
    with open(exclusion_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def save_dataset(output_path: Path, data: List[Dict[str, Any]]):
    """Save the final dataset to CSV."""
    if not data:
        raise ValueError("No data to save")
    
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def calculate_success_rate(total_input: int, total_output: int) -> float:
    """Calculate the success rate of the pipeline."""
    if total_input == 0:
        return 0.0
    return total_output / total_input

def save_success_rate_report(output_path: Path, success_rate: float, total_input: int, total_output: int):
    """Save the success rate report."""
    report = {
        "success_rate": success_rate,
        "total_input_rows": total_input,
        "total_output_rows": total_output,
        "status": "completed"
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def save_post_filter_distribution(output_path: Path, data: List[Dict[str, Any]]):
    """Save the distribution of substrate classes after filtering."""
    distribution = {}
    for row in data:
        cls = row.get('substrate_class', 'unknown')
        distribution[cls] = distribution.get(cls, 0) + 1
    
    with open(output_path, 'w') as f:
        json.dump(distribution, f, indent=2)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(checksum_path: Path, file_path: Path, checksum: str):
    """Save the checksum to a file."""
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {file_path.name}\n")

def save_final_dataset(data: List[Dict[str, Any]], output_path: Path, checksum_path: Path):
    """Save the final dataset and its checksum."""
    save_dataset(output_path, data)
    checksum = compute_file_checksum(output_path)
    save_checksum(checksum_path, output_path, checksum)

def load_split_datasets(split_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load split datasets (train, val, test) if they exist."""
    splits = {}
    for split_name in ['train', 'val', 'test']:
        split_file = split_dir / f"{split_name}_sn1.csv"
        if split_file.exists():
            splits[split_name] = load_processed_data(split_file)
    return splits

def main():
    """Main entry point for dataset finalization."""
    config = DataConfig()
    ensure_dirs()
    log_file = Path(config.log_dir) / "finalize_dataset.log"
    logger = setup_finalize_logger(log_file)

    logger.info("Starting dataset finalization...")

    # Define paths
    input_path = Path(config.intermediate_cleaned_path)
    exclusion_path = Path(config.exclusion_report_path)
    output_path = Path(config.cleaned_sn1_path)
    checksum_path = Path(config.checksum_path)
    success_rate_path = Path(config.success_rate_path)
    distribution_path = Path(config.post_filter_distribution_path)

    # Load data
    try:
        data = load_processed_data(input_path)
        logger.info(f"Loaded {len(data)} rows from {input_path}")
    except FileNotFoundError as e:
        logger.error(f"Fatal error: {e}")
        # Create empty output with status
        with open(output_path, 'w') as f:
            f.write("smiles,rate_constant,substrate_class\n")
        with open(success_rate_path, 'w') as f:
            json.dump({"status": "blocked", "reason": "input_missing"}, f)
        sys.exit(1)

    # Load exclusion report for logging (optional, not strictly needed for merge if clean.py already filtered)
    try:
        exclusions = load_exclusion_report(exclusion_path)
        logger.info(f"Loaded {len(exclusions)} exclusion records")
    except FileNotFoundError as e:
        logger.warning(f"Exclusion report not found: {e}")
        exclusions = []

    # Save final dataset
    save_final_dataset(data, output_path, checksum_path)
    logger.info(f"Saved final dataset to {output_path}")

    # Calculate and save success rate
    # Assuming input to this stage is the intermediate_cleaned which is already filtered
    # We need the raw count from earlier. For now, we calculate based on available data.
    # In a real pipeline, we'd track counts through the stages.
    total_input = len(data) + len(exclusions) # Approximation
    success_rate = calculate_success_rate(total_input, len(data))
    save_success_rate_report(success_rate_path, success_rate, total_input, len(data))
    logger.info(f"Success rate: {success_rate:.4f}")

    # Save distribution
    save_post_filter_distribution(distribution_path, data)
    logger.info(f"Saved distribution to {distribution_path}")

    logger.info("Dataset finalization completed.")

if __name__ == "__main__":
    main()
