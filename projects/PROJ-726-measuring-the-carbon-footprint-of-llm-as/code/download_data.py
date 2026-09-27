import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any

from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "code_x_glue_ct_code_to_code"
# We specifically need the Python subset for code generation tasks
# The dataset structure in HuggingFace Hub for code_x_glue_ct_code_to_code
# typically has 'python' as a split or a specific configuration.
# Based on common usage of CodeXGLUE for Python generation:
DATASET_CONFIG = "python" 
TARGET_SPLIT = "train"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "codexglue_python_dataset.json"
BASELINE_FILE = Path("data/raw/human_baseline_times.json")

def fetch_codexglue_dataset(
    dataset_name: str = DATASET_NAME,
    config: str = DATASET_CONFIG,
    split: str = TARGET_SPLIT,
    streaming: bool = True,
    sample_size: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch the CodeXGLUE Python code-generation dataset.
    
    Args:
        dataset_name: HuggingFace dataset identifier.
        config: Dataset configuration (e.g., 'python').
        split: Data split to load.
        streaming: If True, stream data to avoid loading full dataset into memory.
        sample_size: Optional limit on number of samples to fetch.
        
    Returns:
        List of dictionaries containing prompt and code data.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched or is empty.
    """
    logger.info(f"Fetching dataset: {dataset_name} (config: {config}, split: {split})")
    
    try:
        # Attempt to load dataset
        # Note: CodeXGLUE 'code_to_code' often requires specific handling.
        # We assume the standard 'code_x_glue_ct_code_to_code' structure.
        # If 'python' config doesn't exist directly, we might need to filter.
        # For robustness, we try to load the dataset and handle potential errors.
        
        if streaming:
            ds = load_dataset(dataset_name, config=config, split=split, streaming=True)
        else:
            ds = load_dataset(dataset_name, config=config, split=split)
        
        # Convert to list if not streaming, or iterate if streaming
        if streaming:
            data_list = []
            iterator = iter(ds)
            count = 0
            for item in iterator:
                data_list.append(item)
                count += 1
                if sample_size and count >= sample_size:
                    break
            logger.info(f"Retrieved {count} samples from stream.")
            return data_list
        else:
            if sample_size:
                return ds.select(range(min(sample_size, len(ds)))).to_list()
            return ds.to_list()
            
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_name}: {str(e)}")
        raise RuntimeError(f"Dataset fetch failed: {str(e)}") from e

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_sample_size(data: List[Dict], min_size: int = 1) -> bool:
    """Validate that the fetched data meets minimum sample size requirements."""
    if len(data) < min_size:
        logger.warning(f"Sample size {len(data)} is below minimum {min_size}.")
        return False
    return True

def verify_baseline_exists() -> bool:
    """
    Verify that the human baseline file exists.
    This is a critical check per the Verified Fallback Protocol.
    """
    if not BASELINE_FILE.exists():
        logger.error(f"Human baseline file not found: {BASELINE_FILE}")
        logger.error("Cannot proceed with alternative datasets (HumanEval/MBPP) as no human baseline exists for those prompts.")
        return False
    return True

def save_dataset(data: List[Dict], output_path: Path) -> None:
    """Save the dataset to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Dataset saved to {output_path}")

def validate_checksum(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Validate the checksum of the downloaded file.
    If expected_hash is provided, compare against it.
    """
    if not file_path.exists():
        return False
    
    actual_hash = compute_file_hash(file_path)
    logger.info(f"Computed checksum for {file_path}: {actual_hash}")
    
    if expected_hash:
        if actual_hash == expected_hash:
            logger.info("Checksum validation passed.")
            return True
        else:
            logger.error(f"Checksum mismatch! Expected: {expected_hash}, Got: {actual_hash}")
            return False
    
    return True

def main():
    """
    Main entry point for downloading and validating the CodeXGLUE dataset.
    
    Implements T005 fallback logic:
    - Attempts to fetch CodeXGLUE.
    - If fetch fails, logs error and exits (does NOT switch to HumanEval/MBPP).
    - If fetch succeeds but sample size is small, logs reason and proceeds.
    - Verifies baseline existence before proceeding.
    """
    logger.info("Starting data download process (T005 implementation).")
    
    # 1. Verify baseline exists (T006 dependency check)
    if not verify_baseline_exists():
        logger.critical("Human baseline missing. Aborting download per Verified Fallback Protocol.")
        sys.exit(1)
    
    # 2. Attempt to fetch dataset
    # We try to fetch a reasonable sample size for initial runs, 
    # but the logic handles arbitrary sizes.
    # If the full dataset is too large, we might limit it here or in the caller.
    # For T005, we focus on the failure mode.
    try:
        # Fetching a small sample first to test connectivity and structure
        # In a real run, this might be the full dataset or a specific subset
        data = fetch_codexglue_dataset(sample_size=200) 
        
        if not data:
            raise RuntimeError("Dataset fetch returned empty list.")
            
    except RuntimeError as e:
        # T005: If fetch fails, DO NOT switch to HumanEval/MBPP.
        # Proceed with available sample size (if any) or fail gracefully.
        logger.error(f"CodeXGLUE fetch failed: {str(e)}")
        logger.error("Switching to alternative datasets (HumanEval/MBPP) is NOT permitted per Verified Fallback Protocol.")
        logger.error("Aborting execution due to missing real data source.")
        sys.exit(1)
    
    # 3. Validate sample size
    # T005: If N < 200, log the specific reason for sample size reduction.
    # Here we assume we requested 200. If we got less, we log it.
    if len(data) < 200:
        logger.warning(f"Sample size reduced to {len(data)}. Reason: Dataset availability or network constraints.")
        logger.info(f"Proceeding with available sample size (N={len(data)}).")
    
    # 4. Save dataset
    save_dataset(data, OUTPUT_FILE)
    
    # 5. Validate checksum (placeholder for T008, no expected hash provided yet)
    validate_checksum(OUTPUT_FILE)
    
    logger.info("Data download and validation completed successfully.")

if __name__ == "__main__":
    main()