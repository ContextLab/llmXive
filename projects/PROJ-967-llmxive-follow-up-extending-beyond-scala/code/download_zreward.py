import argparse
import hashlib
import json
import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import requests

# Adjust import to match existing API surface in code/verify_dataset.py
try:
    from verify_dataset import setup_logging as verify_setup_logging, verify_dataset_id
except ImportError:
    # Fallback if verify_dataset is not yet installed in path, though task T000c created it
    def verify_setup_logging():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)
    def verify_dataset_id(dataset_id: str) -> Tuple[bool, str]:
        # Placeholder for verification logic if module missing
        return False, "verify_dataset module not found"

logger = verify_setup_logging()

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESEARCH_MD_PATH = PROJECT_ROOT / "specs" / "001-llmxive-entanglement-analysis" / "research.md"

REQUIRED_COLUMNS = [
    "prompt", "image_url", "student_scalar", "primary_dimension",
    "teacher_scores", "human_annotations"
]

RUBRIC_KEYS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]

DATASET_IDS = [
    "z-reward/z-reward-v1",
    "z-reward/z-reward-v2"
]

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(checksum: str, output_path: Path) -> None:
    """Save checksum to a file."""
    with open(output_path, "w") as f:
        f.write(checksum)

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum."""
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def validate_columns(df: pd.DataFrame) -> Tuple[bool, list]:
    """Validate presence of required columns and nested structures."""
    missing = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)

    # Validate nested structures
    if "teacher_scores" in df.columns:
        # Check if it's a dict-like column or expanded columns
        if isinstance(df["teacher_scores"].iloc[0], dict):
            for key in RUBRIC_KEYS:
                if key not in df["teacher_scores"].iloc[0]:
                    missing.append(f"teacher_scores.{key}")
        else:
            # Expect expanded columns like teacher_scores_Alignment
            for key in RUBRIC_KEYS:
                col_name = f"teacher_scores_{key}"
                if col_name not in df.columns:
                    missing.append(col_name)

    if "human_annotations" in df.columns:
        if isinstance(df["human_annotations"].iloc[0], dict):
            for key in RUBRIC_KEYS:
                if key not in df["human_annotations"].iloc[0]:
                    missing.append(f"human_annotations.{key}")
        else:
            for key in RUBRIC_KEYS:
                col_name = f"human_annotations_{key}"
                if col_name not in df.columns:
                    missing.append(col_name)

    return len(missing) == 0, missing

def load_real_dataset(dataset_id: str) -> Optional[pd.DataFrame]:
    """Load dataset from Hugging Face."""
    logger.info(f"Attempting to load dataset: {dataset_id}")
    try:
        # Check if datasets library is available
        from datasets import load_dataset
        ds = load_dataset(dataset_id, split="train", streaming=False)
        df = ds.to_pandas()
        logger.info(f"Successfully loaded {dataset_id}. Rows: {len(df)}")
        return df
    except Exception as e:
        logger.warning(f"Failed to load {dataset_id}: {e}")
        return None

def download_from_local_archive(archive_path: str) -> Optional[pd.DataFrame]:
    """Load dataset from a local .zip archive."""
    logger.info(f"Attempting to load from local archive: {archive_path}")
    try:
        archive_path = Path(archive_path)
        if not archive_path.exists():
            logger.warning(f"Archive not found: {archive_path}")
            return None

        # Simple extraction logic assuming parquet inside zip
        import zipfile
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)

            # Find parquet file
            parquet_files = list(Path(tmp_dir).rglob("*.parquet"))
            if not parquet_files:
                logger.warning("No parquet file found in archive")
                return None

            df = pd.read_parquet(parquet_files[0])
            logger.info(f"Loaded from archive. Rows: {len(df)}")
            return df
    except Exception as e:
        logger.error(f"Error loading from archive: {e}")
        return None

def generate_synthetic_fallback(n_samples: int = 10000) -> pd.DataFrame:
    """Generate synthetic data for testing if real data is missing in test mode."""
    logger.warning("Generating synthetic fallback data.")
    import numpy as np

    np.random.seed(42)
    data = {
        "prompt": [f"Prompt {i}" for i in range(n_samples)],
        "image_url": [f"http://example.com/img_{i}.jpg" for i in range(n_samples)],
        "student_scalar": np.random.normal(5, 2, n_samples),
        "primary_dimension": np.random.choice(RUBRIC_KEYS, n_samples),
    }

    # Create nested dicts for teacher_scores and human_annotations
    teacher_scores = []
    human_annotations = []
    for _ in range(n_samples):
        teacher_scores.append({k: np.random.normal(5, 2) for k in RUBRIC_KEYS})
        human_annotations.append({k: np.random.normal(5, 2) for k in RUBRIC_KEYS})

    data["teacher_scores"] = teacher_scores
    data["human_annotations"] = human_annotations

    return pd.DataFrame(data)

def parse_args():
    parser = argparse.ArgumentParser(description="Download Z-Reward dataset with adaptive fallback")
    parser.add_argument("--mode", type=str, default="test", choices=["research", "test"],
                        help="Mode: 'research' fails if data missing, 'test' uses synthetic fallback.")
    parser.add_argument("--n-samples", type=int, default=10000, help="Number of synthetic samples if fallback used.")
    return parser.parse_args()

def update_research_md(is_synthetic: bool, dataset_id: Optional[str] = None):
    """Update research.md with verification results."""
    if not RESEARCH_MD_PATH.exists():
        logger.warning("research.md not found, skipping update.")
        return

    content = RESEARCH_MD_PATH.read_text()
    timestamp = pd.Timestamp.now().isoformat()

    # Simple append logic for the verified section
    # In a real scenario, we would parse the YAML/JSON block more robustly
    if "## Verified datasets" not in content:
        content += "\n\n## Verified datasets\n"

    entry = f"- **Dataset ID**: {dataset_id if dataset_id else 'SYNTHETIC'}\n"
    entry += f"  - **Status**: {'Verified' if not is_synthetic else 'Synthetic Fallback'}\n"
    entry += f"  - **Verification Date**: {timestamp}\n"
    entry += f"  - **Note**: {'Real data loaded successfully.' if not is_synthetic else 'Real data unavailable; synthetic fallback used.'}\n"

    RESEARCH_MD_PATH.write_text(content + "\n" + entry)

def main():
    args = parse_args()
    mode = args.mode
    n_samples = args.n_samples

    # Ensure directories exist
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    dataset = None
    used_source = None
    is_synthetic = False
    validation_log = {
        "status": "pending",
        "source": None,
        "errors": [],
        "schema_valid": False
    }

    # 1. Try Real Datasets
    for ds_id in DATASET_IDS:
        df = load_real_dataset(ds_id)
        if df is not None:
            valid, missing = validate_columns(df)
            if valid:
                dataset = df
                used_source = ds_id
                validation_log["status"] = "success"
                validation_log["source"] = ds_id
                validation_log["schema_valid"] = True
                break
            else:
                validation_log["errors"].append(f"{ds_id} missing columns: {missing}")
                logger.warning(f"Dataset {ds_id} schema invalid: {missing}")

    # 2. Try Local Archive
    if dataset is None:
        local_path = os.environ.get("Z_REWARD_ARCHIVE_PATH")
        if local_path:
            df = download_from_local_archive(local_path)
            if df is not None:
                valid, missing = validate_columns(df)
                if valid:
                    dataset = df
                    used_source = f"local:{local_path}"
                    validation_log["status"] = "success"
                    validation_log["source"] = used_source
                    validation_log["schema_valid"] = True

    # 3. Handle Missing Data
    if dataset is None:
        if mode == "research":
            error_msg = "Real data missing in research mode. Aborting."
            logger.error(error_msg)
            validation_log["status"] = "failed"
            validation_log["errors"].append(error_msg)
            raise RuntimeError(error_msg)
        else:
            logger.info("Mode is 'test'. Generating synthetic fallback.")
            dataset = generate_synthetic_fallback(n_samples)
            used_source = "synthetic"
            is_synthetic = True
            validation_log["status"] = "synthetic_fallback"
            validation_log["source"] = "synthetic"

    # 4. Save Outputs
    output_file = DATA_RAW_DIR / "z_reward.parquet"
    if is_synthetic:
        output_file = DATA_RAW_DIR / "z_reward_synthetic.parquet"

    dataset.to_parquet(output_file)
    logger.info(f"Dataset saved to {output_file}")

    # Save Validation Log
    validation_log_path = DATA_RAW_DIR / "validation_log.json"
    with open(validation_log_path, "w") as f:
        json.dump(validation_log, f, indent=2)

    # Calculate valid sample count
    # Filter for non-null and finite values in key columns
    key_cols = ["student_scalar", "prompt", "image_url"]
    # Check teacher_scores and human_annotations complexity
    valid_mask = dataset[key_cols].notna().all(axis=1)
    # Basic check for numeric columns
    for col in ["student_scalar"]:
        if col in dataset.columns:
            valid_mask &= pd.to_numeric(dataset[col], errors='coerce').notna()

    total_samples = len(dataset)
    valid_samples = valid_mask.sum()
    excluded_count = total_samples - valid_samples

    valid_sample_count_path = DATA_PROCESSED_DIR / "valid_sample_count.json"
    with open(valid_sample_count_path, "w") as f:
        json.dump({
            "total_samples": int(total_samples),
            "valid_samples": int(valid_samples),
            "excluded_count": int(excluded_count)
        }, f, indent=2)

    # Update research.md
    update_research_md(is_synthetic, used_source)

    logger.info("Task T037 completed successfully.")

if __name__ == "__main__":
    main()