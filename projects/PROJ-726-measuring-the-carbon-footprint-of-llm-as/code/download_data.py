import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def fetch_codexglue_dataset(output_dir: str = "data/raw") -> Path:
    """
    Fetches the CodeXGLUE Python code-generation subset via HuggingFace datasets.
    Returns the path to the saved dataset directory.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Install it via: pip install datasets")
        raise

    logger.info("Fetching CodeXGLUE Python code-generation dataset from HuggingFace...")
    try:
        # Load the specific subset for Python code generation
        # Using streaming to handle large datasets efficiently if needed, but we need to save locally
        dataset = load_dataset("code_x_glue_ct_code_to_text", "python", split="validation")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save the dataset to parquet for efficient local loading and checksumming
        save_path = output_path / "codexglue_python.parquet"
        dataset.to_parquet(str(save_path))
        
        logger.info(f"Dataset saved to {save_path}")
        return save_path
    except Exception as e:
        logger.error(f"Failed to fetch or save CodeXGLUE dataset: {e}")
        raise

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Computes the hash of a file using the specified algorithm.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def validate_sample_size(dataset_path: Path, min_size: int = 200) -> bool:
    """
    Validates that the downloaded dataset has at least min_size entries.
    """
    try:
        from datasets import load_from_disk
        # Check if it's a parquet file or a dataset directory
        if dataset_path.suffix == ".parquet":
            from datasets import load_dataset
            ds = load_dataset("parquet", data_files=str(dataset_path), split="train")
        else:
            ds = load_from_disk(str(dataset_path))
        
        size = len(ds)
        logger.info(f"Dataset size: {size} entries")
        if size < min_size:
            logger.warning(f"Dataset size ({size}) is below the minimum threshold ({min_size}). "
                           f"Proceeding with reduced sample size as per fallback protocol.")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to validate sample size: {e}")
        raise

def verify_baseline_exists(baseline_path: str = "data/raw/human_baseline_times.json") -> bool:
    """
    Verifies that the human baseline file exists.
    """
    path = Path(baseline_path)
    if not path.exists():
        logger.warning(f"Human baseline file not found at {baseline_path}. "
                       f"Baseline data will be missing for matching.")
        return False
    return True

def save_dataset(dataset, output_path: Path):
    """
    Saves the dataset to the specified path.
    """
    dataset.save_to_disk(str(output_path))
    logger.info(f"Dataset saved to {output_path}")

def validate_checksum(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Validates the checksum of the downloaded file.
    If expected_hash is provided, compares against it.
    Otherwise, computes and logs the hash for verification.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot validate checksum: file not found at {file_path}")
    
    computed_hash = compute_file_hash(file_path)
    logger.info(f"Computed checksum for {file_path.name}: {computed_hash}")
    
    if expected_hash:
        if computed_hash == expected_hash:
            logger.info("Checksum validation PASSED.")
            return True
        else:
            logger.error(f"Checksum validation FAILED. Expected: {expected_hash}, Got: {computed_hash}")
            return False
    
    # If no expected hash is provided, we just log the computed one for manual verification
    logger.info("No expected hash provided. Checksum computed for manual verification.")
    return True

def main():
    """
    Main entry point for downloading and validating the dataset.
    """
    output_dir = "data/raw"
    dataset_path = fetch_codexglue_dataset(output_dir)
    
    # Validate sample size
    validate_sample_size(dataset_path)
    
    # Verify baseline existence (warning only)
    verify_baseline_exists()
    
    # Validate checksum (compute and log, no expected hash provided yet)
    validate_checksum(dataset_path)
    
    logger.info("Data download and initial validation complete.")

if __name__ == "__main__":
    main()