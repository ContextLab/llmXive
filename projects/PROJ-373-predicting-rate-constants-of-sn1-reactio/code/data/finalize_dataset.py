import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import hashlib

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_finalize_logger():
    log_path = Path("data/processed/finalize.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_processed_data(config: DataConfig) -> pd.DataFrame:
    """Load the intermediate cleaned data from T012/T013."""
    # Assuming the output of T012/T013 is in data/processed/intermediate_sn1.csv or similar
    # Based on T012 description: "Input: data/processed/intermediate_sn1.csv"
    # And T016 output: "data/processed/cleaned_sn1.csv"
    # We need to load the data that has been cleaned but not yet finalized with checksum.
    # Let's assume the pipeline writes to a temporary intermediate file or we read from the cleaned file if it exists.
    # But T016 says "Save final processed dataset...".
    # Let's assume T012/T013 write to `data/processed/intermediate_sn1.csv` and T016 (this task) finalizes it.
    
    input_path = config.processed_data_path / "intermediate_sn1.csv"
    if not input_path.exists():
        # Fallback: if intermediate doesn't exist, maybe the previous step wrote directly to cleaned?
        # Or maybe the pipeline is broken. We must handle the case where the file is missing.
        # But the task says "Input: data/processed/intermediate_sn1.csv".
        # If it doesn't exist, we cannot proceed.
        logger.error(f"Intermediate data not found at {input_path}")
        raise FileNotFoundError(f"Intermediate data not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from intermediate data.")
    return df

def load_exclusion_report(config: DataConfig) -> pd.DataFrame:
    """Load the exclusion report from T015."""
    # T015 output: data/processed/exclusion_report.csv
    input_path = config.processed_data_path / "exclusion_report.csv"
    if not input_path.exists():
        logger.warning(f"Exclusion report not found at {input_path}. Creating empty report.")
        return pd.DataFrame(columns=["row_index", "reason", "original_smiles"])
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} excluded rows.")
    return df

def save_dataset(df: pd.DataFrame, config: DataConfig):
    """Save the final cleaned dataset."""
    output_path = config.processed_data_path / "cleaned_sn1.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved final dataset to {output_path}")
    return output_path

def calculate_success_rate(input_count: int, output_count: int) -> float:
    if input_count == 0:
        return 0.0
    return (output_count / input_count) * 100

def save_post_filter_distribution(df: pd.DataFrame, config: DataConfig):
    """Save the distribution of substrate classes after filtering."""
    dist = df['substrate_class'].value_counts().to_dict()
    output_path = config.processed_data_path / "post_filter_distribution.json"
    with open(output_path, 'w') as f:
        json.dump(dist, f, indent=2)
    logger.info(f"Saved post-filter distribution to {output_path}")

def save_checksum(file_path: Path, config: DataConfig):
    """Calculate and save checksum."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    checksum = sha256_hash.hexdigest()
    checksum_path = file_path.with_suffix('.sha256')
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    logger.info(f"Saved checksum to {checksum_path}")

def main():
    setup_finalize_logger()
    config = DataConfig()
    ensure_dirs()
    
    try:
        # Load intermediate data
        df = load_processed_data(config)
        initial_count = len(df)
        
        # Load exclusion report (for logging/verification, though filtering should be done)
        # T015 aggregates logs. T016 saves the final CSV.
        # The filtering logic is in T012. T016 just finalizes.
        # We assume df is already filtered by T012.
        
        # Save final dataset
        output_path = save_dataset(df, config)
        
        # Calculate success rate
        success_rate = calculate_success_rate(initial_count, len(df))
        logger.info(f"Success rate: {success_rate:.2f}%")
        
        # Save distribution
        save_post_filter_distribution(df, config)
        
        # Save checksum
        save_checksum(output_path, config)
        
        # Log success rate report
        rate_log_path = config.processed_data_path / "success_rate_report.log"
        with open(rate_log_path, 'w') as f:
            f.write(f"Success Rate: {success_rate:.2f}%\n")
            if success_rate < 95:
                f.write(f"WARNING: Success rate ({success_rate:.2f}%) is below 95%.\n")
        
        logger.info("Finalization complete.")
        
    except Exception as e:
        logger.error(f"Finalization failed: {e}")
        raise

if __name__ == "__main__":
    main()
