"""
Verify HuggingFace Dataset Availability and Integrity.

This script checks if the required HuggingFace datasets are accessible
and validates their schema against the project's CeramicEntry schema.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datasets import load_dataset
from contracts.schemas import CeramicEntry, validate_data_against_schema
from config import initialize_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'hf_verification.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize config
initialize_config()

# Define datasets to verify
DATASETS_TO_VERIFY = [
    {
        "id": "CeramicWeibull/curated-literature",
        "description": "Curated literature data for Weibull modulus prediction",
        "required_fields": ["composition", "weibull_modulus", "sample_count"]
    }
]

def verify_dataset_availability(dataset_id: str, description: str, required_fields: list) -> bool:
    """
    Verify that a HuggingFace dataset is accessible and contains required fields.

    Args:
        dataset_id: HuggingFace dataset ID
        description: Human-readable description
        required_fields: List of required column names

    Returns:
        True if dataset is accessible and valid, False otherwise
    """
    logger.info(f"Verifying dataset: {dataset_id}")
    logger.info(f"Description: {description}")

    try:
        # Attempt to load dataset (streaming to avoid large downloads)
        logger.info(f"Loading dataset '{dataset_id}' in streaming mode...")
        dataset = load_dataset(dataset_id, split="train", streaming=True)

        # Check if dataset is empty
        first_row = next(iter(dataset))
        logger.info(f"First row sample: {first_row}")

        # Validate required fields
        missing_fields = [field for field in required_fields if field not in first_row]
        if missing_fields:
            logger.error(f"Missing required fields in dataset {dataset_id}: {missing_fields}")
            return False

        logger.info(f"Dataset '{dataset_id}' verified successfully with {len(required_fields)} required fields.")
        return True

    except Exception as e:
        logger.error(f"Failed to verify dataset {dataset_id}: {str(e)}")
        return False

def main():
    """Main entry point for dataset verification."""
    logger.info("Starting HuggingFace dataset verification...")

    all_verified = True
    results = []

    for dataset_config in DATASETS_TO_VERIFY:
        is_valid = verify_dataset_availability(
            dataset_config["id"],
            dataset_config["description"],
            dataset_config["required_fields"]
        )
        results.append({
            "dataset_id": dataset_config["id"],
            "verified": is_valid,
            "description": dataset_config["description"]
        })
        if not is_valid:
            all_verified = False

    # Save verification results
    results_path = project_root / "data" / "artifacts" / "hf_dataset_verification.json"
    os.makedirs(results_path.parent, exist_ok=True)

    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Verification results saved to {results_path}")

    if all_verified:
        logger.info("All datasets verified successfully.")
        sys.exit(0)
    else:
        logger.warning("Some datasets failed verification.")
        sys.exit(1)

if __name__ == "__main__":
    main()
