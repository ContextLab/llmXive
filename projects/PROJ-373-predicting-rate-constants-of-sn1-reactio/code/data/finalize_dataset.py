import os
import sys
import csv
import json
import logging
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from local modules based on API surface provided
from config import DataConfig, ensure_dirs
from utils.logger import get_logger

def setup_finalize_logger(log_path: Path) -> logging.Logger:
    """Set up the logger for the finalize dataset task."""
    ensure_dirs(log_path.parent)
    logger = get_logger("finalize_dataset", log_path)
    return logger

def load_processed_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load the cleaned intermediate dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def load_exclusion_report(exclusion_path: Path) -> List[Dict[str, Any]]:
    """Load the exclusion report if it exists."""
    if not exclusion_path.exists():
        return []
    
    data = []
    with open(exclusion_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def save_dataset(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the final processed dataset to CSV."""
    ensure_dirs(output_path.parent)
    if not data:
        # Write empty file with headers if needed, or just create empty file
        # Based on task, we expect data to be present if success_rate passes
        pass 
    
    fieldnames = data[0].keys() if data else []
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def calculate_success_rate(final_count: int, input_count: int) -> float:
    """Calculate the success rate of the pipeline."""
    if input_count == 0:
        return 0.0
    return final_count / input_count

def save_success_rate_report(success_rate: float, status: str, reason: Optional[str], output_path: Path) -> None:
    """Save the success rate report to JSON."""
    ensure_dirs(output_path.parent)
    report = {
        "status": status,
        "success_rate": success_rate,
        "reason": reason
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Compute the checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def save_checksum(checksum: str, output_path: Path) -> None:
    """Save the checksum to a file."""
    ensure_dirs(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(checksum)

def save_final_dataset(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Wrapper to save final dataset."""
    save_dataset(data, output_path)

def main(args: Optional[argparse.Namespace] = None) -> int:
    """Main entry point for T016: Finalize dataset and calculate success rate."""
    if args is None:
        parser = argparse.ArgumentParser(description="Finalize dataset and calculate success rate")
        parser.add_argument("--input-path", type=str, required=True, help="Path to cleaned intermediate CSV")
        parser.add_argument("--intermediate-path", type=str, required=True, help="Path to intermediate SN1 CSV (for success rate calc)")
        parser.add_argument("--output-path", type=str, required=True, help="Path to save final cleaned CSV")
        parser.add_argument("--exclusion-path", type=str, required=True, help="Path to exclusion report CSV")
        parser.add_argument("--success-rate-path", type=str, required=True, help="Path to save success rate JSON")
        parser.add_argument("--checksum-path", type=str, required=True, help="Path to save checksum file")
        parser.add_argument("--threshold", type=float, default=0.95, help="Success rate threshold")
        args = parser.parse_args()

    input_path = Path(args.input_path)
    intermediate_path = Path(args.intermediate_path)
    output_path = Path(args.output_path)
    exclusion_path = Path(args.exclusion_path)
    success_rate_path = Path(args.success_rate_path)
    checksum_path = Path(args.checksum_path)
    threshold = args.threshold

    logger = setup_finalize_logger(output_path.with_suffix('.log'))
    logger.info(f"Starting finalize dataset task. Input: {input_path}, Intermediate: {intermediate_path}")

    try:
        # Load cleaned data
        if not input_path.exists():
            raise FileNotFoundError(f"Input file {input_path} not found")
        
        cleaned_data = load_processed_data(input_path)
        logger.info(f"Loaded {len(cleaned_data)} rows from {input_path}")

        # Load intermediate data to calculate success rate
        if not intermediate_path.exists():
            raise FileNotFoundError(f"Intermediate file {intermediate_path} not found")
        
        intermediate_data = load_processed_data(intermediate_path)
        logger.info(f"Loaded {len(intermediate_data)} rows from {intermediate_path}")

        # Calculate success rate
        success_rate = calculate_success_rate(len(cleaned_data), len(intermediate_data))
        logger.info(f"Calculated success rate: {success_rate:.4f} (Threshold: {threshold})")

        # Check threshold
        if success_rate < threshold:
            logger.error(f"Success rate {success_rate} is below threshold {threshold}")
            save_success_rate_report(success_rate, "FAIL", "success_rate_below_threshold", success_rate_path)
            logger.error("Pipeline halted due to low success rate.")
            return 1

        # Save success rate
        save_success_rate_report(success_rate, "PASS", None, success_rate_path)
        logger.info("Success rate check passed.")

        # Save final dataset
        save_final_dataset(cleaned_data, output_path)
        logger.info(f"Saved final dataset to {output_path}")

        # Compute and save checksum
        checksum = compute_file_checksum(output_path)
        save_checksum(checksum, checksum_path)
        logger.info(f"Saved checksum to {checksum_path}")

        logger.info("Finalize dataset task completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Fatal error in finalize dataset task: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
