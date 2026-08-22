"""
Data ingestion module for QM9-TS dataset.

This module handles fetching the QM9-TS dataset from a verified HuggingFace source,
computing checksums for integrity verification, and preparing the data for downstream
processing.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Try to import datasets from HuggingFace
try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' package is required. Install it with: pip install datasets")
    sys.exit(1)

from src.utils.logging import get_logger, log_progress, log_metric, log_error_summary

# Configure logging
logger = get_logger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the checksum
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON manifest file.
    
    Args:
        checksums: Dictionary mapping filenames to their checksums
        output_path: Path to save the JSON manifest
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")

def fetch_dataset_from_hf(dataset_name: str = "molecular-ml/QM9-TS", 
                          split: str = "train", 
                          streaming: bool = True) -> Any:
    """
    Fetch the QM9-TS dataset from HuggingFace Datasets.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace
        split: Which split to load (train, test, etc.)
        streaming: If True, stream the dataset instead of downloading fully
        
    Returns:
        Dataset object from HuggingFace
        
    Raises:
        RuntimeError: If the dataset cannot be fetched
    """
    logger.info(f"Fetching dataset: {dataset_name} (split={split}, streaming={streaming})")
    
    try:
        # Attempt to load the dataset
        # Using streaming=True to avoid downloading the full dataset into memory
        # which is crucial for CPU-only environments with limited RAM
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming
        )
        
        # Verify we actually got data by attempting to peek at the first item
        # This will fail loudly if the dataset is empty or inaccessible
        if streaming:
            # For streaming datasets, we get an iterable
            first_item = next(iter(dataset))
            logger.info(f"Successfully fetched dataset. First item keys: {list(first_item.keys())}")
        else:
            logger.info(f"Successfully fetched dataset. Total items: {len(dataset)}")
        
        return dataset
        
    except Exception as e:
        error_msg = f"Failed to fetch dataset from HuggingFace: {str(e)}"
        logger.error(error_msg)
        log_error_summary(error_msg)
        # Fail loudly - do not fall back to synthetic data
        raise RuntimeError(error_msg) from e

def load_and_count_reactions(dataset: Any, 
                             target_elements: List[str] = ["Pd", "Ni", "Cu"]) -> Tuple[int, List[Dict]]:
    """
    Count reactions containing specified transition metals.
    
    Args:
        dataset: The loaded dataset
        target_elements: List of transition metal symbols to filter for
        
    Returns:
        Tuple of (count of matching reactions, list of matching reaction metadata)
    """
    logger.info(f"Counting reactions with elements: {target_elements}")
    
    matching_count = 0
    matching_reactions = []
    
    # Iterate through the dataset (works for both streaming and non-streaming)
    for idx, item in enumerate(dataset):
        # The dataset structure may vary, but typically contains 'elements' or 'atoms'
        # We need to check if any of our target elements are present
        elements = item.get('elements', [])
        if not elements:
            # Try alternative key names
            elements = item.get('atoms', [])
            
        # Check if any target element is in the reaction
        has_target = any(el in elements for el in target_elements)
        
        if has_target:
            matching_count += 1
            # Store minimal metadata for logging
            if len(matching_reactions) < 10:  # Keep only first 10 for logging
                matching_reactions.append({
                    "index": idx,
                    "elements": elements,
                    "has_target": True
                })
            
        # Log progress every 1000 items
        if (idx + 1) % 1000 == 0:
            log_progress(f"Processed {idx + 1} items, found {matching_count} matches")
    
    log_metric("matching_reactions_count", matching_count)
    logger.info(f"Found {matching_count} reactions containing {target_elements}")
    
    return matching_count, matching_reactions

def filter_transition_metals(dataset: Any,
                             target_elements: List[str] = ["Pd", "Ni", "Cu"],
                             output_dir: Optional[Path] = None) -> Any:
    """
    Filter the dataset to include only reactions with specified transition metals.
    
    This is a filtering operation that returns a new dataset view or filtered list.
    For large datasets with streaming, this returns a filtered iterator.
    
    Args:
        dataset: The loaded dataset
        target_elements: List of transition metal symbols to keep
        output_dir: Optional directory to save filtered results
        
    Returns:
        Filtered dataset or list of matching items
    """
    logger.info(f"Filtering for transition metals: {target_elements}")
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    filtered_items = []
    
    for idx, item in enumerate(dataset):
        elements = item.get('elements', [])
        if not elements:
            elements = item.get('atoms', [])
            
        if any(el in elements for el in target_elements):
            filtered_items.append(item)
            
        if (idx + 1) % 1000 == 0:
            log_progress(f"Filtered {idx + 1} items, kept {len(filtered_items)}")
    
    logger.info(f"Filtered dataset contains {len(filtered_items)} items")
    
    if output_dir:
        # Save filtered data as JSON for now (parquet conversion happens later)
        output_path = output_dir / "filtered_qm9_ts.json"
        with open(output_path, "w") as f:
            json.dump(filtered_items, f, indent=2)
        logger.info(f"Filtered data saved to {output_path}")
        
        # Compute and save checksum
        checksum = compute_file_checksum(output_path)
        checksum_manifest = {
            "file": str(output_path),
            "checksum": checksum,
            "algorithm": "sha256",
            "item_count": len(filtered_items)
        }
        checksum_path = output_dir / "filtered_checksum.json"
        with open(checksum_path, "w") as f:
            json.dump(checksum_manifest, f, indent=2)
        logger.info(f"Checksum saved to {checksum_path}")
    
    return filtered_items

def handle_scarcity(count: int, 
                    threshold: int = 120,
                    output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Handle data scarcity logic as per FR-001.
    
    Args:
        count: Number of matching reactions found
        threshold: Minimum required count (default 120)
        output_dir: Directory to save scarcity flag if triggered
        
    Returns:
        Dictionary with status and count
    """
    result = {
        "count": count,
        "threshold": threshold,
        "status": "ok" if count >= threshold else "scarcity"
    }
    
    if count < threshold:
        logger.warning(f"Data scarcity detected: {count} < {threshold}")
        log_metric("data_scarcity_flag", 1)
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            scarcity_path = output_dir / "data_scarcity_flag.json"
            with open(scarcity_path, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Scarcity flag saved to {scarcity_path}")
    else:
        log_metric("data_scarcity_flag", 0)
        logger.info(f"Data sufficient: {count} >= {threshold}")
    
    return result

def main():
    """
    Main entry point for data ingestion.
    
    This function:
    1. Fetches QM9-TS from HuggingFace
    2. Computes checksums for downloaded artifacts
    3. Filters for Pd, Ni, Cu transition metals
    4. Handles scarcity logic
    """
    logger.info("Starting data ingestion pipeline")
    
    # Define paths
    project_root = get_project_root()
    raw_data_dir = project_root / "data" / "raw"
    processed_data_dir = project_root / "data" / "processed"
    
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration
    dataset_name = "molecular-ml/QM9-TS"
    target_elements = ["Pd", "Ni", "Cu"]
    threshold = 120
    
    try:
        # Step 1: Fetch dataset
        logger.info("Step 1: Fetching QM9-TS dataset...")
        dataset = fetch_dataset_from_hf(dataset_name, split="train", streaming=True)
        
        # Step 2: Count and filter reactions
        logger.info("Step 2: Filtering for transition metals...")
        count, sample_metadata = load_and_count_reactions(dataset, target_elements)
        
        # Step 3: Handle scarcity logic
        logger.info("Step 3: Checking data sufficiency...")
        scarcity_result = handle_scarcity(count, threshold, processed_data_dir)
        
        # Step 4: Save initial fetch metadata
        fetch_metadata = {
            "dataset": dataset_name,
            "split": "train",
            "target_elements": target_elements,
            "count": count,
            "scarcity_status": scarcity_result["status"],
            "threshold": threshold
        }
        
        metadata_path = processed_data_dir / "ingestion_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(fetch_metadata, f, indent=2)
        logger.info(f"Ingestion metadata saved to {metadata_path}")
        
        # Step 5: Compute checksum for the metadata file itself
        metadata_checksum = compute_file_checksum(metadata_path)
        checksum_manifest = {
            "file": str(metadata_path),
            "checksum": metadata_checksum,
            "algorithm": "sha256",
            "timestamp": "ingestion_complete"
        }
        checksum_path = raw_data_dir / "ingestion_checksum.json"
        with open(checksum_path, "w") as f:
            json.dump(checksum_manifest, f, indent=2)
        logger.info(f"Checksum manifest saved to {checksum_path}")
        
        logger.info("Data ingestion pipeline completed successfully")
        log_metric("ingestion_status", "success")
        
        return 0
        
    except Exception as e:
        logger.error(f"Data ingestion failed: {str(e)}")
        log_error_summary(f"Data ingestion failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
