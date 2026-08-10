"""
Data loader module for llmXive pipeline.
Handles fetching, validating, and caching of research datasets.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator

import datasets
from datasets import Dataset, DatasetDict
from huggingface_hub import hf_hub_download, login

from ..config import CONFIG, get_data_path
from ..utils import setup_logger, log_error

# Initialize logger
logger = setup_logger(__name__)

# Constants
WISE_VERIFIED_DATASET_ID = "llmXive/WISE-Verified"  # Verified source ID from plan.md
WISE_VERIFIED_FILES = {
    "prompts": "prompts.jsonl",
    "images": "images.parquet",
    "metadata": "metadata.jsonl"
}

def fetch_wise_verified_dataset(
    output_dir: Optional[str] = None,
    streaming: bool = False
) -> Dict[str, Any]:
    """
    Fetch the WISE-Verified dataset from Hugging Face.
    
    Args:
        output_dir: Directory to save downloaded data. Defaults to CONFIG.data_raw_dir.
        streaming: If True, stream the dataset without downloading fully.
    
    Returns:
        Dictionary containing the dataset splits and metadata.
    
    Raises:
        RuntimeError: If the dataset fetch fails.
        ValueError: If the dataset ID does not match the verified source.
    """
    # Validate dataset ID against plan.md specification
    if WISE_VERIFIED_DATASET_ID != CONFIG.verified_dataset_id:
        error_msg = (
            f"Dataset ID mismatch: Expected '{CONFIG.verified_dataset_id}', "
            f"got '{WISE_VERIFIED_DATASET_ID}'. "
            "This indicates a configuration error or unauthorized dataset source."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    if output_dir is None:
        output_dir = str(get_data_path("raw/wise-verified"))

    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Fetching WISE-Verified dataset from {WISE_VERIFIED_DATASET_ID} to {output_dir}")

    try:
        if streaming:
            # Stream the dataset to avoid memory issues
            dataset = datasets.load_dataset(
                WISE_VERIFIED_DATASET_ID,
                streaming=True,
                trust_remote_code=True
            )
            logger.info("WISE-Verified dataset loaded in streaming mode")
        else:
            # Download full dataset
            dataset = datasets.load_dataset(
                WISE_VERIFIED_DATASET_ID,
                trust_remote_code=True
            )
            logger.info("WISE-Verified dataset downloaded successfully")

            # Save dataset to disk
            dataset.save_to_disk(output_dir)
            logger.info(f"WISE-Verified dataset saved to {output_dir}")

        return {
            "dataset": dataset,
            "path": output_dir,
            "source": WISE_VERIFIED_DATASET_ID,
            "streaming": streaming
        }

    except Exception as e:
        error_msg = (
            f"Failed to fetch WISE-Verified dataset from '{WISE_VERIFIED_DATASET_ID}': {str(e)}. "
            "This is a real data fetch failure. No synthetic fallback is allowed. "
            "Please verify network connectivity and dataset availability."
        )
        logger.error(error_msg)
        # Fail loudly - no synthetic fallback
        raise RuntimeError(error_msg) from e

def validate_wise_verified_schema(dataset: Dataset, expected_fields: List[str]) -> None:
    """
    Validate that the WISE-Verified dataset contains the expected schema.
    
    Args:
        dataset: The loaded dataset to validate.
        expected_fields: List of required field names.
    
    Raises:
        ValueError: If the schema does not match.
    """
    if not isinstance(dataset, (Dataset, DatasetDict)):
        raise ValueError("Invalid dataset type. Expected Dataset or DatasetDict.")

    # Get the first split if it's a DatasetDict
    if isinstance(dataset, DatasetDict):
        first_split = list(dataset.keys())[0]
        dataset = dataset[first_split]

    # Check if dataset is empty
    if len(dataset) == 0:
        raise ValueError("WISE-Verified dataset is empty.")

    # Validate schema
    actual_fields = set(dataset.column_names)
    missing_fields = set(expected_fields) - actual_fields

    if missing_fields:
        error_msg = (
            f"WISE-Verified dataset schema mismatch. Missing required fields: {missing_fields}. "
            f"Available fields: {actual_fields}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"WISE-Verified dataset schema validated successfully. Fields: {actual_fields}")

def compute_wise_verified_checksum(dataset_path: str) -> str:
    """
    Compute and store a checksum for the WISE-Verified dataset.
    
    Args:
        dataset_path: Path to the downloaded dataset.
    
    Returns:
        SHA256 checksum of the dataset directory.
    """
    checksum = hashlib.sha256()
    
    for root, _, files in os.walk(dataset_path):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    checksum.update(chunk)
    
    checksum_hex = checksum.hexdigest()
    logger.info(f"WISE-Verified dataset checksum computed: {checksum_hex}")
    return checksum_hex

def store_artifact_hash(hash_value: str, artifact_name: str = "wise_verified") -> None:
    """
    Store the artifact hash in the state directory.
    
    Args:
        hash_value: The checksum hash to store.
        artifact_name: Name of the artifact for the hash file.
    """
    state_dir = Path(CONFIG.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    hash_file = state_dir / f"{artifact_name}_hash.txt"
    with open(hash_file, "w") as f:
        f.write(hash_value)
    
    logger.info(f"Artifact hash stored in {hash_file}")

def load_wise_verified_references(output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load human-verified reference descriptions from the WISE-Verified dataset.
    
    Args:
        output_dir: Optional directory to save the extracted references.
    
    Returns:
        List of reference descriptions.
    """
    if output_dir is None:
        output_dir = str(get_data_path("raw/wise-verified"))

    references_file = Path(output_dir) / "references.jsonl"
    
    if references_file.exists():
        logger.info(f"Loading existing references from {references_file}")
        with open(references_file, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    # Fetch dataset if references not found
    data = fetch_wise_verified_dataset(output_dir=output_dir)
    dataset = data["dataset"]
    
    # Validate schema for references
    expected_fields = ["prompt_id", "reference_description", "image_path"]
    validate_wise_verified_schema(dataset, expected_fields)
    
    # Extract references
    references = []
    for item in dataset:
        if "reference_description" in item and item["reference_description"]:
            references.append({
                "prompt_id": item["prompt_id"],
                "reference_description": item["reference_description"],
                "image_path": item.get("image_path", "")
            })
    
    # Save references
    if references:
        with open(references_file, "w", encoding="utf-8") as f:
            for ref in references:
                f.write(json.dumps(ref) + "\n")
        logger.info(f"Saved {len(references)} references to {references_file}")
    else:
        logger.warning("No valid references found in WISE-Verified dataset.")
    
    return references

def validate_references_schema(references: List[Dict[str, Any]]) -> None:
    """
    Validate that references contain the required 'reference_description' field.
    
    Args:
        references: List of reference dictionaries.
    
    Raises:
        ValueError: If validation fails.
    """
    if not references:
        raise ValueError("References list is empty.")
    
    for i, ref in enumerate(references):
        if "reference_description" not in ref:
            raise ValueError(f"Reference at index {i} is missing 'reference_description' field.")
        if not ref["reference_description"] or not ref["reference_description"].strip():
            raise ValueError(f"Reference at index {i} has empty 'reference_description'.")
    
    logger.info(f"Validated {len(references)} references successfully.")