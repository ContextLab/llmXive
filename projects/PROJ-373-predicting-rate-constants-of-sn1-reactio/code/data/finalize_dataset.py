import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_finalize_logger():
    """Setup logging for dataset finalization."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "finalize_dataset.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_processed_data(file_path: str):
    """Load the processed CSV file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    import pandas as pd
    return pd.read_csv(file_path)

def load_exclusion_report(file_path: str):
    """Load the exclusion report CSV."""
    if not os.path.exists(file_path):
        logger.warning(f"Exclusion report not found: {file_path}")
        return pd.DataFrame(columns=['row_index', 'reason', 'original_smiles'])
    
    import pandas as pd
    return pd.read_csv(file_path)

def save_dataset(df, output_path: str):
    """Save the final dataset to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Dataset saved to {output_path}")

def calculate_success_rate(final_count: int, input_count: int) -> float:
    """Calculate the success rate of the pipeline."""
    if input_count == 0:
        return 0.0
    return final_count / input_count

def save_success_rate_report(success_rate: float, status: str, output_path: str):
    """Save the success rate report."""
    report = {
        'success_rate': success_rate,
        'status': status,
        'threshold': 0.95
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Success rate report saved to {output_path}")

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(file_path: str, checksum: str, output_path: str):
    """Save the checksum to a file."""
    with open(output_path, 'w') as f:
        f.write(f"{checksum}  {os.path.basename(file_path)}\n")
    logger.info(f"Checksum saved to {output_path}")

def save_final_dataset(df, output_path: str):
    """Save the final dataset (alias for save_dataset)."""
    save_dataset(df, output_path)

def main():
    parser = argparse.ArgumentParser(description="Finalize the processed dataset")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_intermediate.csv",
                      help="Input cleaned intermediate dataset")
    parser.add_argument("--exclusion-report", type=str, default="data/processed/exclusion_report.csv",
                      help="Input exclusion report")
    parser.add_argument("--output", type=str, default="data/processed/cleaned_sn1.csv",
                      help="Output final dataset")
    parser.add_argument("--raw-input", type=str, default="data/raw/sn1_raw.parquet",
                      help="Path to raw input dataset for success rate calculation")
    parser.add_argument("--success-rate-output", type=str, default="data/processed/success_rate.json",
                      help="Output path for success rate report")
    parser.add_argument("--checksum-output", type=str, default="data/processed/cleaned_sn1.csv.sha256",
                      help="Output path for checksum file")
    args = parser.parse_args()

    setup_finalize_logger()
    ensure_dirs()

    try:
        # Load input data
        logger.info(f"Loading input data from {args.input}")
        df = load_processed_data(args.input)
        
        if df.empty:
            logger.error("Input dataset is empty")
            with open("data/processed/clean.log", 'w') as f:
                json.dump({'status': 'fatal_error', 'reason': 'input_missing'}, f)
            sys.exit(1)

        # Load raw data for success rate calculation
        try:
            if args.raw_input.endswith('.parquet'):
                import pandas as pd
                raw_df = pd.read_parquet(args.raw_input)
                raw_count = len(raw_df)
            else:
                raw_count = count_rows(args.raw_input)
        except Exception as e:
            logger.warning(f"Could not load raw data for success rate: {e}")
            raw_count = len(df) * 2  # Estimate if raw data unavailable

        # Calculate success rate
        success_rate = calculate_success_rate(len(df), raw_count)
        logger.info(f"Success rate: {success_rate:.4f}")

        # Check threshold
        if success_rate < 0.95:
            logger.error(f"Success rate {success_rate:.4f} is below threshold 0.95")
            save_success_rate_report(success_rate, 'FAIL', args.success_rate_output)
            sys.exit(1)

        # Verify non-null descriptors
        if 'gasteiger_charges' in df.columns:
            null_count = df['gasteiger_charges'].isna().sum()
            if null_count > 0:
                logger.warning(f"Found {null_count} rows with null gasteiger charges")

        # Save final dataset
        save_dataset(df, args.output)

        # Save success rate report
        save_success_rate_report(success_rate, 'PASS', args.success_rate_output)

        # Compute and save checksum
        checksum = compute_file_checksum(args.output)
        save_checksum(args.output, checksum, args.checksum_output)

        logger.info("Dataset finalization completed successfully")

    except Exception as e:
        logger.error(f"Fatal error during finalization: {e}")
        with open("data/processed/clean.log", 'w') as f:
            json.dump({'status': 'fatal_error', 'reason': str(e)}, f)
        sys.exit(1)

def count_rows(file_path: str) -> int:
    """Count rows in a CSV file."""
    if not os.path.exists(file_path):
        return 0
    with open(file_path, 'r') as f:
        return sum(1 for _ in f) - 1  # Exclude header

if __name__ == "__main__":
    main()
