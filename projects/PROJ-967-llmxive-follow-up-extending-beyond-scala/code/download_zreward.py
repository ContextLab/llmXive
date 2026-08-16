import argparse
import hashlib
import json
import logging
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

REQUIRED_COLUMNS = [
    "prompt",
    "image_url",
    "teacher_scores",
    "student_scalar",
    "human_annotations",
    "primary_dimension"
]

RUBRIC_KEYS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(checksum: str, output_path: str):
    with open(output_path, "w") as f:
        f.write(checksum)

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def validate_columns(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """Validate that the dataframe contains all required columns and nested structures."""
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False

    # Validate nested structures for teacher_scores and human_annotations
    try:
        first_row = df.iloc[0]
        if not isinstance(first_row["teacher_scores"], dict):
            logger.error("teacher_scores is not a dictionary")
            return False
        if not all(k in first_row["teacher_scores"] for k in RUBRIC_KEYS):
            logger.error(f"teacher_scores missing keys: {set(RUBRIC_KEYS) - set(first_row['teacher_scores'].keys())}")
            return False

        if not isinstance(first_row["human_annotations"], dict):
            logger.error("human_annotations is not a dictionary")
            return False
        if not all(k in first_row["human_annotations"] for k in RUBRIC_KEYS):
            logger.error(f"human_annotations missing keys: {set(RUBRIC_KEYS) - set(first_row['human_annotations'].keys())}")
            return False
    except Exception as e:
        logger.error(f"Error validating nested structures: {e}")
        return False

    return True

def load_real_dataset(dataset_id: str, logger: logging.Logger) -> pd.DataFrame:
    """Attempt to load the dataset from Hugging Face."""
    try:
        logger.info(f"Attempting to load dataset: {dataset_id}")
        dataset = load_dataset(dataset_id, split="train")
        df = dataset.to_pandas()
        logger.info(f"Successfully loaded {len(df)} rows from {dataset_id}")
        return df
    except Exception as e:
        logger.warning(f"Failed to load {dataset_id}: {e}")
        return None

def download_from_local_archive(archive_path: str, extract_dir: str, logger: logging.Logger) -> pd.DataFrame:
    """Extract and load from a local zip archive."""
    try:
        logger.info(f"Attempting to load from local archive: {archive_path}")
        if not os.path.exists(archive_path):
            logger.error(f"Archive not found: {archive_path}")
            return None

        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Look for parquet or csv files in the extracted directory
        extracted_files = list(Path(extract_dir).rglob("*.parquet")) + list(Path(extract_dir).rglob("*.csv"))
        if not extracted_files:
            logger.error("No data files found in archive")
            return None

        data_file = extracted_files[0]
        if data_file.suffix == '.parquet':
            df = pd.read_parquet(data_file)
        else:
            df = pd.read_csv(data_file)

        logger.info(f"Successfully loaded {len(df)} rows from archive")
        return df
    except Exception as e:
        logger.error(f"Failed to load from archive: {e}")
        return None

def generate_synthetic_fallback(output_path: str, logger: logging.Logger, n_rows: int = 10000) -> pd.DataFrame:
    """Generate synthetic data when all real sources fail."""
    logger.warning("All real data sources failed. Invoking synthetic fallback.")
    import numpy as np

    np.random.seed(42)
    data = {
        "prompt": [f"Sample prompt {i}" for i in range(n_rows)],
        "image_url": [f"https://example.com/img_{i}.jpg" for i in range(n_rows)],
        "teacher_scores": [
            {k: float(np.random.normal(5, 2)) for k in RUBRIC_KEYS}
            for _ in range(n_rows)
        ],
        "student_scalar": list(np.random.normal(5, 2, n_rows)),
        "human_annotations": [
            {k: float(np.random.normal(5, 2)) for k in RUBRIC_KEYS}
            for _ in range(n_rows)
        ],
        "primary_dimension": [np.random.choice(RUBRIC_KEYS) for _ in range(n_rows)]
    }

    df = pd.DataFrame(data)
    df.to_parquet(output_path, index=False)
    logger.info(f"Synthetic dataset saved to {output_path}")
    return df

def parse_args():
    parser = argparse.ArgumentParser(description="Download Z-Reward dataset")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory")
    parser.add_argument("--output-file", type=str, default="z_reward.parquet", help="Output filename")
    parser.add_argument("--log-file", type=str, default="validation_log.json", help="Validation log filename")
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / args.output_file
    log_file = output_dir / args.log_file

    validation_result = {
        "status": "failed",
        "source": None,
        "rows": 0,
        "columns_validated": False,
        "fallback_used": False,
        "message": ""
    }

    df = None

    # 1. Primary Source
    df = load_real_dataset("z-reward/z-reward-v1", logger)
    if df is not None:
        validation_result["source"] = "z-reward/z-reward-v1"
        validation_result["status"] = "success"

    # 2. Secondary Source
    if df is None:
        df = load_real_dataset("z-reward/z-reward-v2", logger)
        if df is not None:
            validation_result["source"] = "z-reward/z-reward-v2"
            validation_result["status"] = "success"

    # 3. Local Archive
    if df is None:
        archive_path = os.getenv("Z_REWARD_ARCHIVE_PATH")
        if archive_path:
            extract_dir = output_dir / "archive_extract"
            df = download_from_local_archive(archive_path, str(extract_dir), logger)
            if df is not None:
                validation_result["source"] = f"local_archive:{archive_path}"
                validation_result["status"] = "success"

    # 4. Adaptive Fallback (Synthetic) - ONLY if all real sources failed
    if df is None:
        logger.warning("All real data sources failed. Generating synthetic fallback.")
        synthetic_path = output_dir / "z_reward_synthetic.parquet"
        df = generate_synthetic_fallback(str(synthetic_path), logger)
        validation_result["status"] = "success_fallback"
        validation_result["fallback_used"] = True
        validation_result["message"] = "Synthetic fallback invoked due to missing real data."
        output_file = synthetic_path  # Update output path for synthetic file

    # Validate columns if we have data
    if df is not None:
        if validate_columns(df, logger):
            validation_result["columns_validated"] = True
            df.to_parquet(output_file, index=False)
            validation_result["rows"] = len(df)
            validation_result["checksum"] = calculate_sha256(str(output_file))
            logger.info(f"Data saved to {output_file}")
        else:
            validation_result["message"] = "Schema validation failed."
            validation_result["status"] = "failed_schema"
    else:
        validation_result["message"] = "No data source available."
        validation_result["status"] = "failed_no_source"

    # Write validation log
    with open(log_file, "w") as f:
        json.dump(validation_result, f, indent=2)
    logger.info(f"Validation log saved to {log_file}")

    if validation_result["status"].startswith("failed") and not validation_result["fallback_used"]:
        logger.error("Pipeline failed to load real data and synthetic fallback was not invoked.")
        sys.exit(1)

    logger.info("Task T037 completed successfully.")

if __name__ == "__main__":
    main()