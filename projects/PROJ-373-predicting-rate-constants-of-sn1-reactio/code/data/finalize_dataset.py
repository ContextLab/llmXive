import os
import sys
import csv
import json
import logging
import argparse
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Constants
DATA_CONFIG = DataConfig()

def setup_finalize_logger() -> logging.Logger:
    """Setup logging for the finalize dataset stage."""
    logger = get_logger("finalize_dataset")
    logger.setLevel(logging.INFO)
    return logger

def load_processed_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load processed data from a CSV file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def load_exclusion_report(exclusion_path: Path) -> List[Dict[str, Any]]:
    """Load exclusion report from a CSV file."""
    if not exclusion_path.exists():
        # If exclusion report doesn't exist, return empty list
        # This might happen if no exclusions were made
        return []
    
    data = []
    with open(exclusion_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def save_dataset(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the final dataset to a CSV file."""
    if not data:
        raise ValueError("Cannot save empty dataset")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def calculate_success_rate(original_count: int, final_count: int) -> float:
    """Calculate the success rate of the pipeline."""
    if original_count == 0:
        return 0.0
    return (final_count / original_count) * 100

def save_success_rate_report(success_rate: float, original_count: int, final_count: int, output_path: Path) -> None:
    """Save the success rate report to a JSON file."""
    report = {
        "success_rate": success_rate,
        "original_count": original_count,
        "final_count": final_count,
        "status": "completed"
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def save_post_filter_distribution(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the distribution of substrate classes after filtering."""
    distribution = {}
    for row in data:
        substrate_class = row.get('substrate_class', 'unknown')
        distribution[substrate_class] = distribution.get(substrate_class, 0) + 1
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(distribution, f, indent=2)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(file_path: Path, checksum: str, output_path: Path) -> None:
    """Save the checksum to a text file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {file_path.name}\n")

def save_final_dataset(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the final dataset to a CSV file (alias for save_dataset)."""
    save_dataset(data, output_path)

def load_split_datasets(split_path: Path) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Load the train, validation, and test splits from CSV files.
    Returns a tuple of (train_data, val_data, test_data).
    """
    train_path = split_path / "train.csv"
    val_path = split_path / "validation.csv"
    test_path = split_path / "test.csv"
    
    def load_split(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"smiles": [], "rate_constant": [], "substrate_class": []}
        
        data = {"smiles": [], "rate_constant": [], "substrate_class": []}
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data["smiles"].append(row.get("smiles", ""))
                data["rate_constant"].append(float(row.get("rate_constant", 0)))
                data["substrate_class"].append(row.get("substrate_class", "unknown"))
        return data
    
    return load_split(train_path), load_split(val_path), load_split(test_path)

def main():
    """Main entry point for the finalize dataset stage."""
    parser = argparse.ArgumentParser(description="Finalize the processed dataset")
    parser.add_argument("--input", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "cleaned_intermediate.csv"),
                      help="Path to the cleaned intermediate CSV file")
    parser.add_argument("--exclusion-report", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "exclusion_report.csv"),
                      help="Path to the exclusion report CSV file")
    parser.add_argument("--output", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "cleaned_sn1.csv"),
                      help="Path to save the final cleaned dataset")
    parser.add_argument("--checksum-output", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "cleaned_sn1.csv.sha256"),
                      help="Path to save the checksum file")
    parser.add_argument("--success-rate-output", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "success_rate.json"),
                      help="Path to save the success rate report")
    parser.add_argument("--distribution-output", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "post_filter_distribution.json"),
                      help="Path to save the post-filter distribution")
    
    args = parser.parse_args()
    
    logger = setup_finalize_logger()
    logger.info("Starting finalize dataset stage")
    
    try:
        # Ensure directories exist
        ensure_dirs(DATA_CONFIG)
        
        input_path = Path(args.input)
        exclusion_path = Path(args.exclusion_report)
        output_path = Path(args.output)
        checksum_output_path = Path(args.checksum_output)
        success_rate_output_path = Path(args.success_rate_output)
        distribution_output_path = Path(args.distribution_output)
        
        # Load processed data
        logger.info(f"Loading processed data from {input_path}")
        processed_data = load_processed_data(input_path)
        original_count = len(processed_data)
        logger.info(f"Loaded {original_count} rows")
        
        # Load exclusion report (for logging purposes)
        exclusion_data = load_exclusion_report(exclusion_path)
        logger.info(f"Loaded {len(exclusion_data)} exclusion records")
        
        # Save the final dataset
        logger.info(f"Saving final dataset to {output_path}")
        save_dataset(processed_data, output_path)
        
        # Calculate and save success rate
        final_count = len(processed_data)
        success_rate = calculate_success_rate(original_count, final_count)
        logger.info(f"Success rate: {success_rate:.2f}%")
        save_success_rate_report(success_rate, original_count, final_count, success_rate_output_path)
        
        # Save post-filter distribution
        logger.info("Saving post-filter distribution")
        save_post_filter_distribution(processed_data, distribution_output_path)
        
        # Compute and save checksum
        checksum = compute_file_checksum(output_path)
        logger.info(f"Checksum: {checksum}")
        save_checksum(output_path, checksum, checksum_output_path)
        
        logger.info("Finalize dataset stage completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during finalize dataset stage: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
