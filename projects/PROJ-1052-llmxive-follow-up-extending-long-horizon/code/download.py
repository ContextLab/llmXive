"""
Download and validate the AgentBench dataset.

This script fetches the 'lmz/agentbench' dataset from Hugging Face,
saves it to 'data/raw/', performs cryptographic hash validation,
and verifies the presence of required variables (observations, actions, rewards).
"""
import hashlib
import logging
import os
import sys
from pathlib import Path

from datasets import load_dataset

# Configuration
DATASET_ID = "lmz/agentbench"
OUTPUT_DIR = Path("data/raw")
# Expected checksum for the dataset archive (example placeholder; 
# in a real scenario, this would be the verified SHA-256 from the dataset card).
# Since the specific split file checksums vary by version, we will validate
# the integrity of the download via the datasets library's built-in checks
# and log the actual hash of the downloaded file for verification.
# If a specific checksum is mandated by the spec, it should be updated here.
EXPECTED_SHA256 = None  # Replace with actual hash if known from documentation

# Required variables for the research pipeline
REQUIRED_VARIABLES = ["observations", "actions", "rewards"]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/download.log", mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_variables(dataset, dataset_id: str) -> None:
    """
    Verify that the dataset contains the required variables: observations, actions, rewards.
    
    Raises:
        ValueError: If any required variable is missing, with error code ERR_MISSING_VAR.
    """
    missing_vars = []
    available_columns = set(dataset.column_names)
    
    for var in REQUIRED_VARIABLES:
        if var not in available_columns:
            missing_vars.append(var)
    
    if missing_vars:
        error_msg = f"ERR_MISSING_VAR: The dataset '{dataset_id}' is missing required variables: {missing_vars}. " \
                    f"Available columns: {list(available_columns)}."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"✓ Validation PASSED: All required variables {REQUIRED_VARIABLES} found in '{dataset_id}'.")

def main():
    """Main entry point for downloading, validating, and checking the dataset."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting download and validation for dataset '{DATASET_ID}'...")

    try:
        # Log the substitution note as per task requirements
        logger.info("ℹ Note: 'Long-Horizon-Terminal-Bench' was substituted with 'AgentBench' (lmz/agentbench).")

        # Load the dataset
        # We use streaming=False to download the full dataset for local validation
        logger.info(f"Loading dataset '{DATASET_ID}' split='train'...")
        dataset = load_dataset(DATASET_ID, split="train", trust_remote_code=True)
        
        # Save the dataset to disk in Parquet format for efficiency
        output_path = OUTPUT_DIR / "agentbench.parquet"
        logger.info(f"Saving dataset to: {output_path}")
        dataset.to_parquet(str(output_path))

        # Calculate and log the hash of the downloaded file
        actual_hash = calculate_sha256(output_path)
        logger.info(f"Calculated SHA-256: {actual_hash}")

        if EXPECTED_SHA256:
            if actual_hash == EXPECTED_SHA256:
                logger.info("✓ Checksum verification PASSED.")
            else:
                logger.error(f"✗ Checksum verification FAILED.")
                logger.error(f"  Expected: {EXPECTED_SHA256}")
                logger.error(f"  Actual:   {actual_hash}")
                sys.exit(1)
        else:
            logger.warning("⚠ No expected checksum provided for verification. "
                         "Please verify the hash against the dataset documentation manually.")

        # Validate required variables
        logger.info("Validating required variables (observations, actions, rewards)...")
        validate_variables(dataset, DATASET_ID)

        logger.info("Dataset download and validation completed successfully.")

    except ValueError as e:
        if "ERR_MISSING_VAR" in str(e):
            logger.error(f"Validation failed: {e}")
            sys.exit(1)
        else:
            logger.error(f"Unexpected error during validation: {e}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error downloading or processing dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()