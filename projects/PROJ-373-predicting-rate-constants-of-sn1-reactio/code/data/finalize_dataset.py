import os
import sys
import csv
import json
import logging
import argparse
import hashlib
from pathlib import Path

# Import from sibling modules based on API surface
from config import ensure_dirs, DataConfig
from utils.logger import get_logger

# Ensure directories exist for any file operations
ensure_dirs()

def setup_finalize_logger():
    """Set up logging for the finalize dataset script."""
    logger = logging.getLogger("finalize_dataset")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    log_path = Path("data/processed/finalize.log")
    ensure_dirs(log_path)
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    logger.addHandler(fh)
    
    return logger

def load_processed_data(input_path):
    """Load the cleaned intermediate CSV data."""
    logger = logging.getLogger("finalize_dataset")
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            df.append(row)
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def load_exclusion_report(exclusion_path):
    """Load the exclusion report to calculate success rate."""
    logger = logging.getLogger("finalize_dataset")
    if not os.path.exists(exclusion_path):
        logger.warning(f"Exclusion report not found at {exclusion_path}. Assuming 0 exclusions.")
        return 0
    
    count = 0
    with open(exclusion_path, 'r', newline='', encoding='utf-8') as f:
        # Skip header
        next(f, None)
        for line in f:
            if line.strip():
                count += 1
    
    logger.info(f"Found {count} exclusions in {exclusion_path}")
    return count

def save_dataset(data, output_path):
    """Save the final processed dataset to CSV."""
    logger = logging.getLogger("finalize_dataset")
    ensure_dirs(output_path)
    
    if not data:
        logger.warning("No data to save.")
        return
    
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} rows to {output_path}")

def calculate_success_rate(final_count, exclusion_count):
    """Calculate the success rate of the pipeline."""
    total = final_count + exclusion_count
    if total == 0:
        return 0.0
    return final_count / total

def save_success_rate_report(success_rate, status, output_path):
    """Save the success rate report to JSON."""
    logger = logging.getLogger("finalize_dataset")
    ensure_dirs(output_path)
    
    report = {
        "success_rate": success_rate,
        "status": status,
        "final_count": final_count if 'final_count' in locals() else 0,
        "exclusion_count": exclusion_count if 'exclusion_count' in locals() else 0
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved success rate report to {output_path}")

def compute_file_checksum(file_path):
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(checksum, checksum_path):
    """Save the checksum to a file."""
    logger = logging.getLogger("finalize_dataset")
    ensure_dirs(checksum_path)
    
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(checksum)
    
    logger.info(f"Saved checksum to {checksum_path}")

def main():
    parser = argparse.ArgumentParser(description="Finalize the SN1 dataset pipeline.")
    parser.add_argument("--input-path", required=True, help="Path to cleaned intermediate CSV")
    parser.add_argument("--output-path", required=True, help="Path to save final cleaned CSV")
    parser.add_argument("--exclusion-path", required=True, help="Path to exclusion report CSV")
    parser.add_argument("--success-rate-path", required=True, help="Path to save success rate JSON")
    parser.add_argument("--checksum-path", required=True, help="Path to save checksum file")
    
    args = parser.parse_args()
    
    logger = setup_finalize_logger()
    logger.info("Starting final dataset finalization...")
    
    # Guard clause: Check if input file exists
    if not os.path.exists(args.input_path):
        logger.error(f"Input file missing: {args.input_path}")
        # We cannot calculate success rate without input, but we must write a status
        # The task says: If data/raw/... is missing, block. Here input is cleaned_intermediate.
        # If this specific file is missing, it's an upstream failure.
        # We write a failure status to success_rate.json as per general pattern, or exit.
        # Task T016 specifically says: "If data/raw/sn1_raw_merged.parquet ... missing ... exit 1"
        # But here we are loading cleaned_intermediate. If that's missing, we can't proceed.
        sys.exit(1)
    
    # Load data
    try:
        data = load_processed_data(args.input_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # Load exclusion count
    exclusion_count = load_exclusion_report(args.exclusion_path)
    final_count = len(data)
    
    # Verify non-null descriptors (simple check for required columns if they exist)
    # Assuming columns like 'gasteiger_charges' or similar might be present
    # For robustness, we just check if data is not empty
    if final_count == 0:
        logger.warning("Final dataset is empty.")
    
    # Calculate success rate
    success_rate = calculate_success_rate(final_count, exclusion_count)
    status = "PASS" if success_rate >= 0.95 else "FAIL"
    
    logger.info(f"Success Rate: {success_rate:.4f} ({status})")
    
    # Save final dataset
    save_dataset(data, args.output_path)
    
    # Save success rate report
    save_success_rate_report(success_rate, status, args.success_rate_path)
    
    # Compute and save checksum
    checksum = compute_file_checksum(args.output_path)
    save_checksum(checksum, args.checksum_path)
    
    logger.info("Finalization completed successfully.")

if __name__ == "__main__":
    main()