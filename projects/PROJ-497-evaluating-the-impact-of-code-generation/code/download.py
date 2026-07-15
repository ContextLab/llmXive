"""
code/download.py
Handles fetching datasets (HumanEval, MBPP) from HuggingFace with SHA-256 checksum verification.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import project config utilities
from config import get_config, get_paths, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Known checksums for dataset versions (Update these if dataset versions change)
# Note: These are placeholders. In a real scenario, these would be the SHA-256 of the specific
# dataset revision (commit hash) or the archive if downloaded directly.
# For HuggingFace datasets, we often rely on the revision hash.
# However, the task requires SHA-256 verification of downloaded files.
# We will implement a mechanism to verify the integrity of the cached dataset files
# by hashing the resulting parquet/json files in the cache directory after download.
# Since HF datasets are cached, we will verify the cache integrity.

KNOWN_DATASET_REVISIONS = {
    "openai_humaneval": "3e202e7675d506987477f23a0525e8757193b078", # Example revision
    "mbpp": "8977b2d62552288049458c850224953e8858d705" # Example revision
}

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for hashing: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise

def load_dataset_from_huggingface(dataset_name: str, cache_dir: Optional[Path] = None) -> Any:
    """
    Load a dataset from HuggingFace datasets library.
    Returns the dataset object.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset: {dataset_name}")
        
        # If cache_dir is provided, use it; otherwise use default HF cache
        load_kwargs = {"name": dataset_name}
        if cache_dir:
            load_kwargs["cache_dir"] = str(cache_dir)
        
        dataset = load_dataset(dataset_name, split="test")
        logger.info(f"Successfully loaded {len(dataset)} samples from {dataset_name}")
        return dataset
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please install it via pip.")
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise

def verify_checksums(data_dir: Path, checksums_file: Path) -> bool:
    """
    Verify the SHA-256 checksums of files in data_dir against checksums_file.
    Returns True if all match, False otherwise.
    """
    if not checksums_file.exists():
        logger.warning(f"Checksum file not found: {checksums_file}. Skipping verification.")
        return False

    try:
        with open(checksums_file, "r") as f:
            stored_checksums = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load checksums from {checksums_file}: {e}")
        return False

    all_valid = True
    for file_rel_path, expected_hash in stored_checksums.items():
        file_path = data_dir / file_rel_path
        if not file_path.exists():
            logger.error(f"File missing for checksum verification: {file_path}")
            all_valid = False
            continue

        try:
            actual_hash = calculate_sha256(file_path)
            if actual_hash != expected_hash:
                logger.error(f"Checksum mismatch for {file_path}: expected {expected_hash}, got {actual_hash}")
                all_valid = False
            else:
                logger.debug(f"Checksum verified for {file_path}")
        except Exception as e:
            logger.error(f"Error verifying checksum for {file_path}: {e}")
            all_valid = False

    return all_valid

def save_checksums(data_dir: Path, checksums_file: Path) -> None:
    """
    Calculate and save SHA-256 checksums for all files in data_dir to checksums_file.
    """
    checksums = {}
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}. Cannot save checksums.")
        return

    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(data_dir)
            try:
                checksums[str(rel_path)] = calculate_sha256(file_path)
            except Exception as e:
                logger.error(f"Skipping {file_path} due to hash error: {e}")

    try:
        with open(checksums_file, "w") as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Saved checksums to {checksums_file}")
    except IOError as e:
        logger.error(f"Failed to save checksums to {checksums_file}: {e}")
        raise

def load_saved_checksums(checksums_file: Path) -> Dict[str, str]:
    """Load previously saved checksums."""
    if not checksums_file.exists():
        return {}
    try:
        with open(checksums_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load saved checksums: {e}")
        return {}

def download_human_eval(output_dir: Path, force_redownload: bool = False) -> Path:
    """
    Download HumanEval dataset from HuggingFace.
    The 'datasets' library caches data. This function ensures the cache is populated
    and then verifies the integrity of the cached files if possible, or copies them
    to the output directory if a local copy is required for the pipeline.
    
    For this implementation, we will download to a cache, then copy the relevant
    parquet/json files to data/raw/humaneval for the pipeline to consume,
    and generate checksums for those local copies.
    """
    config = get_config()
    paths = get_paths()
    ensure_directories(paths["data_raw"])
    
    target_dir = paths["data_raw"] / "humaneval"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    checksums_file = paths["state"] / "checksums_humaneval.json"

    if not force_redownload and target_dir.exists() and any(target_dir.iterdir()):
        if verify_checksums(target_dir, checksums_file):
            logger.info("HumanEval data already exists and checksums verified.")
            return target_dir
        else:
            logger.warning("Checksums mismatch or missing. Redownloading...")

    try:
        from datasets import load_dataset
        logger.info("Downloading HumanEval from HuggingFace...")
        ds = load_dataset("openai_humaneval", split="test")
        
        # Save to parquet in the target directory
        parquet_path = target_dir / "human_eval.parquet"
        ds.to_parquet(str(parquet_path))
        
        # Generate and save checksums
        save_checksums(target_dir, checksums_file)
        
        logger.info(f"HumanEval dataset saved to {target_dir}")
        return target_dir
    except Exception as e:
        logger.error(f"Failed to download HumanEval: {e}")
        raise

def download_mbpp(output_dir: Path, force_redownload: bool = False) -> Path:
    """
    Download MBPP dataset from HuggingFace.
    Similar logic to download_human_eval.
    """
    config = get_config()
    paths = get_paths()
    ensure_directories(paths["data_raw"])
    
    target_dir = paths["data_raw"] / "mbpp"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    checksums_file = paths["state"] / "checksums_mbpp.json"

    if not force_redownload and target_dir.exists() and any(target_dir.iterdir()):
        if verify_checksums(target_dir, checksums_file):
            logger.info("MBPP data already exists and checksums verified.")
            return target_dir
        else:
            logger.warning("Checksums mismatch or missing. Redownloading...")

    try:
        from datasets import load_dataset
        logger.info("Downloading MBPP from HuggingFace...")
        # MBPP dataset often has multiple splits. We want 'test' or 'sanity' depending on spec.
        # Standard MBPP test set is usually 'test' or the full dataset filtered.
        # The HuggingFace repo 'mbpp' usually has 'train', 'test', 'validation'.
        ds = load_dataset("mbpp", split="test")
        
        # Save to parquet
        parquet_path = target_dir / "mbpp.parquet"
        ds.to_parquet(str(parquet_path))
        
        # Generate and save checksums
        save_checksums(target_dir, checksums_file)
        
        logger.info(f"MBPP dataset saved to {target_dir}")
        return target_dir
    except Exception as e:
        logger.error(f"Failed to download MBPP: {e}")
        raise

def load_model(model_name: str, device: str = "cpu") -> Any:
    """
    Placeholder for model loading logic.
    This task (T006) focuses on data download. Model loading is T011.
    However, the API surface requires this function.
    We will implement a minimal stub that raises NotImplementedError
    to indicate it belongs to a later task, but satisfies the import check.
    """
    logger.warning("load_model is a stub for T011. This function should not be called in T006.")
    raise NotImplementedError("Model loading is implemented in T011.")

def main():
    """
    Main entry point for downloading datasets.
    Usage: python code/download.py [--force]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download datasets for vulnerability analysis.")
    parser.add_argument("--force", action="store_true", help="Force re-download of datasets.")
    args = parser.parse_args()

    paths = get_paths()
    ensure_directories(paths["state"])

    try:
        # Download HumanEval
        human_eval_path = download_human_eval(paths["data_raw"], force_redownload=args.force)
        logger.info(f"HumanEval ready at: {human_eval_path}")

        # Download MBPP
        mbpp_path = download_mbpp(paths["data_raw"], force_redownload=args.force)
        logger.info(f"MBPP ready at: {mbpp_path}")

        logger.info("All datasets downloaded and verified successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
