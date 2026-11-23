"""
Download and verify the Z-Reward evaluation dataset.

This script implements the strict fallback logic required by T037:
1. Primary: Verify via reference-validator (simulated here by checking existence/validity).
2. Secondary: Check environment variable Z_REWARD_ARCHIVE_PATH for local archive.
3. Fail Loud: If neither works, raise RuntimeError.

No synthetic fallback is permitted.
"""
import argparse
import hashlib
import json
import logging
import os
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List

# Try to import datasets; if not available, we handle it gracefully but fail loud if needed
try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    logging.warning("HuggingFace datasets library not installed. Will attempt local archive only.")

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """Validate that the DataFrame contains all required columns."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def load_real_dataset() -> Optional[pd.DataFrame]:
    """
    Attempt to load the real Z-Reward dataset via HuggingFace.
    Returns None if unavailable.
    """
    if not DATASETS_AVAILABLE:
        logger.info("HuggingFace datasets library not available, skipping primary source.")
        return None

    try:
        logger.info("Attempting to load 'z-reward' dataset from HuggingFace...")
        # The task description suggests 'z-reward' as the ID.
        # If the exact ID is different in reality, this will fail and we fall back to local.
        dataset = load_dataset("z-reward", split="train")
        df = dataset.to_pandas()
        
        # Basic sanity check: does it have any rows?
        if len(df) == 0:
            logger.warning("Dataset loaded but has 0 rows.")
            return None
        
        logger.info(f"Successfully loaded {len(df)} samples from HuggingFace.")
        return df
    except Exception as e:
        logger.warning(f"Failed to load from HuggingFace ('z-reward'): {e}")
        return None

def download_from_local_archive(archive_path: str, output_dir: str) -> Optional[pd.DataFrame]:
    """
    Extract a local archive (zip/tar.gz) to output_dir and load the parquet/csv.
    Returns None if extraction or loading fails.
    """
    logger.info(f"Attempting to load from local archive: {archive_path}")
    
    if not os.path.exists(archive_path):
        logger.error(f"Archive file not found: {archive_path}")
        return None

    extraction_dir = Path(output_dir) / "z_reward_extracted"
    extraction_dir.mkdir(parents=True, exist_ok=True)

    try:
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extraction_dir)
        elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extraction_dir)
        elif archive_path.endswith('.tar'):
            with tarfile.open(archive_path, 'r') as tar_ref:
                tar_ref.extractall(extraction_dir)
        else:
            logger.error(f"Unsupported archive format: {archive_path}")
            return None

        # Look for parquet or csv files in the extracted directory
        data_file = None
        for ext in ['.parquet', '.csv']:
            matches = list(extraction_dir.rglob(f"*{ext}"))
            if matches:
                data_file = matches[0]
                break
        
        if not data_file:
            logger.error("No .parquet or .csv file found in the extracted archive.")
            return None

        logger.info(f"Found data file: {data_file}")
        if data_file.suffix == '.parquet':
            df = pd.read_parquet(data_file)
        else:
            df = pd.read_csv(data_file)

        if len(df) == 0:
            logger.error("Extracted dataset is empty.")
            return None

        logger.info(f"Successfully loaded {len(df)} samples from local archive.")
        return df

    except Exception as e:
        logger.error(f"Failed to extract/load archive: {e}")
        return None

def save_validation_log(log_data: Dict[str, Any], output_path: str):
    """Save the validation log to JSON."""
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Validation log saved to {output_path}")

def save_sample_count(count_data: Dict[str, int], output_path: str):
    """Save the sample count to JSON."""
    with open(output_path, 'w') as f:
        json.dump(count_data, f, indent=2)
    logger.info(f"Sample count saved to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Download and verify Z-Reward dataset")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Directory to save raw data")
    parser.add_argument("--validation-log", type=str, default="data/raw/validation_log.json", help="Path to validation log")
    parser.add_argument("--sample-count", type=str, default="data/processed/valid_sample_count.json", help="Path to sample count file")
    return parser.parse_args()

def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure data/processed exists for the sample count file
    Path(args.sample_count).parent.mkdir(parents=True, exist_ok=True)

    required_columns = [
        'prompt', 'image_url', 'teacher_scores', 'student_scalar', 
        'human_annotations', 'primary_dimension'
    ]

    df: Optional[pd.DataFrame] = None
    source: Optional[str] = None
    status: str = "failed"
    message: str = ""
    checksum: str = ""

    # 1. Primary: Try HuggingFace
    if DATASETS_AVAILABLE:
        df = load_real_dataset()
        if df is not None:
            source = "huggingface_z_reward"
            status = "success"
            # Calculate checksum of the first few rows or a hash of the data
            # For simplicity, we hash the string representation of the first 1000 rows
            sample_str = str(df.head(1000).to_dict())
            checksum = hashlib.sha256(sample_str.encode()).hexdigest()
    
    # 2. Secondary: Try Local Archive
    if df is None:
        archive_path = os.getenv("Z_REWARD_ARCHIVE_PATH")
        if archive_path:
            df = download_from_local_archive(archive_path, str(output_dir))
            if df is not None:
                source = "local_archive"
                status = "success"
                checksum = calculate_sha256(archive_path)
                message = f"Loaded from local archive: {archive_path}"
        else:
            message = "No Z_REWARD_ARCHIVE_PATH environment variable set."

    # 3. Fail Loud if no data
    if df is None:
        logger.error("No real data found. Synthetic fallback is prohibited by FR-006/Constitution Principle VII.")
        # We still write the validation log to indicate failure
        validation_log = {
            "source": "none",
            "status": "failed",
            "message": "No real data found. Pipeline halting.",
            "schema_valid": False,
            "sample_count": 0
        }
        save_validation_log(validation_log, args.validation_log)
        # Write empty/zero count
        save_sample_count({"total_samples": 0, "valid_samples": 0, "excluded_count": 0}, args.sample_count)
        raise RuntimeError("No real data found. Synthetic fallback is prohibited by FR-006/Constitution Principle VII.")

    # 4. Validate Schema
    if not validate_columns(df, required_columns):
        logger.error("Schema validation failed.")
        validation_log = {
            "source": source,
            "status": "failed",
            "message": "Schema validation failed: missing required columns.",
            "schema_valid": False,
            "sample_count": len(df)
        }
        save_validation_log(validation_log, args.validation_log)
        raise RuntimeError("Schema validation failed.")

    # 5. Save Outputs
    output_file = output_dir / "z_reward.parquet"
    df.to_parquet(output_file, index=False)
    logger.info(f"Saved dataset to {output_file}")

    validation_log = {
        "source": source,
        "status": status,
        "message": message or "Dataset loaded and validated successfully.",
        "schema_valid": True,
        "sample_count": len(df),
        "checksum": checksum
    }
    save_validation_log(validation_log, args.validation_log)

    total_samples = len(df)
    # For this task, we assume all loaded samples are valid initially.
    # Exclusions will be handled by T014/T024.
    valid_samples = total_samples
    excluded_count = 0

    save_sample_count({
        "total_samples": total_samples,
        "valid_samples": valid_samples,
        "excluded_count": excluded_count
    }, args.sample_count)

    logger.info("T037 completed successfully.")

if __name__ == "__main__":
    main()
