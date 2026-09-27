"""
Reference Validator for Crystal Structure Prediction Dataset.

This module implements the Reference-Validator integration required by
Constitution Principle II. It verifies the HuggingFace dataset citation
against the primary source (Crystallography Open Database) before processing.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from huggingface_hub import HfApi, hf_hub_download

from config import get_path_absolute
from logging_config import get_logger, log_event
from exceptions import DownloadError, ValidationError

logger = get_logger(__name__)

# Primary Source Configuration
# The project targets the organic subset of the Crystallography Open Database (COD)
# hosted on HuggingFace.
TARGET_DATASET_ID = "crystallography-open-database/organic"
EXPECTED_LICENSE = "CC0-1.0"
EXPECTED_AUTHOR = "Crystallography Open Database"
REQUIRED_CITATION_KEY = "cod_citation"

# Path to store the validation manifest
VALIDATION_MANIFEST_PATH = "data/validation/source_citation_manifest.json"


def get_dataset_metadata(dataset_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches metadata for a specific dataset from HuggingFace Hub.

    Args:
        dataset_id: The HuggingFace dataset identifier (e.g., 'author/dataset').
        token: Optional HuggingFace token for private datasets.

    Returns:
        A dictionary containing dataset metadata (author, license, etc.).

    Raises:
        DownloadError: If the dataset cannot be accessed or does not exist.
    """
    try:
        api = HfApi(token=token)
        # Fetch dataset info
        dataset_info = api.dataset_info(dataset_id=dataset_id)

        return {
            "id": dataset_info.id,
            "author": dataset_info.author,
            "license": getattr(dataset_info, 'cardData', {}).get('license', 'unknown'),
            "citation": getattr(dataset_info, 'cardData', {}).get('citation', ''),
            "description": getattr(dataset_info, 'cardData', {}).get('description', ''),
            "last_modified": str(dataset_info.lastModified) if dataset_info.lastModified else None
        }
    except Exception as e:
        logger.error(f"Failed to fetch metadata for dataset {dataset_id}: {e}")
        raise DownloadError(f"Unable to access dataset {dataset_id} on HuggingFace Hub. "
                            f"Ensure the dataset exists and credentials are valid.") from e


def verify_citation(metadata: Dict[str, Any], expected_author: str, expected_license: str) -> bool:
    """
    Verifies the dataset citation details against expected values.

    Args:
        metadata: The dataset metadata dictionary.
        expected_author: The expected author/organization name.
        expected_license: The expected license identifier.

    Returns:
        True if the citation matches expectations.

    Raises:
        ValidationError: If the author or license does not match.
    """
    author = metadata.get("author", "")
    license_type = metadata.get("license", "")

    # Normalize strings for comparison
    author_match = expected_author.lower() in author.lower()
    license_match = expected_license.lower() == license_type.lower()

    if not author_match:
        error_msg = (
            f"Citation Author Mismatch: Expected '{expected_author}', "
            f"got '{author}'."
        )
        logger.error(error_msg)
        raise ValidationError(error_msg)

    if not license_match:
        error_msg = (
            f"Citation License Mismatch: Expected '{expected_license}', "
            f"got '{license_type}'."
        )
        logger.error(error_msg)
        raise ValidationError(error_msg)

    logger.info(f"Citation verified: Author='{author}', License='{license_type}'")
    return True


def save_validation_manifest(metadata: Dict[str, Any], verification_status: str, output_path: str):
    """
    Saves the validation result to a JSON manifest file.

    Args:
        metadata: The dataset metadata.
        verification_status: 'PASSED' or 'FAILED'.
        output_path: File path for the manifest.
    """
    manifest = {
        "dataset_id": metadata.get("id"),
        "author": metadata.get("author"),
        "license": metadata.get("license"),
        "verification_status": verification_status,
        "timestamp": log_event("validation_complete", {"status": verification_status})["timestamp"]
    }

    # Ensure directory exists
    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(path_obj, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Validation manifest saved to {output_path}")


def validate_source(dataset_id: str = TARGET_DATASET_ID) -> bool:
    """
    Main entry point for validating the data source.

    This function:
    1. Fetches metadata from HuggingFace.
    2. Verifies the author and license against project requirements.
    3. Saves a validation manifest.

    Args:
        dataset_id: The HuggingFace dataset ID to validate.

    Returns:
        True if validation passes.

    Raises:
        ValidationError: If citation verification fails.
        DownloadError: If metadata cannot be fetched.
    """
    logger.info(f"Starting source validation for dataset: {dataset_id}")

    # 1. Fetch Metadata
    metadata = get_dataset_metadata(dataset_id)

    # 2. Verify Citation (Constitution Principle II)
    # We strictly enforce the author and license to ensure we are using
    # the official COD organic subset and not a spoofed or incorrect mirror.
    verify_citation(metadata, EXPECTED_AUTHOR, EXPECTED_LICENSE)

    # 3. Save Manifest
    output_path = get_path_absolute(VALIDATION_MANIFEST_PATH)
    save_validation_manifest(metadata, "PASSED", output_path)

    logger.info("Source validation completed successfully.")
    return True


def main():
    """
    CLI entry point for the validator.
    """
    try:
        validate_source()
        print("Validation successful. Dataset is approved for processing.")
        return 0
    except ValidationError as e:
        print(f"Validation Failed: {e}")
        return 1
    except DownloadError as e:
        print(f"Download/Access Error: {e}")
        return 2
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 3


if __name__ == "__main__":
    import sys
    sys.exit(main())
