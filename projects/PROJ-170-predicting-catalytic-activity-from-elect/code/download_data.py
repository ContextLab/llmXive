"""
Data download and verification module for the OC20 dataset.

This module handles downloading the stratified sample of the OC20 dataset
from HuggingFace, verifying checksums, and deriving composition families.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import h5py
from datasets import load_dataset
from pymatgen.core import Composition
from config import get_project_root, get_data_path
from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
DATASET_ID = "Open-Catalyst/oc20-experimental"
FILE_NAME = "oc20.h5"
OUTPUT_PATH = "data/raw/oc20_sample.h5"
CHECKSUM_FILE = "data/raw/checksums.json"
STRATIFICATION_COLUMN = "composition_family"
SAMPLE_SIZE = 1000  # Stratified sample size

def load_expected_checksums() -> Dict[str, str]:
    """Load expected checksums from the checksum file."""
    checksum_path = get_project_root() / CHECKSUM_FILE
    if checksum_path.exists():
        with open(checksum_path, 'r') as f:
            return json.load(f)
    return {}

def save_checksum(filename: str, checksum: str) -> None:
    """Save a checksum for a downloaded file."""
    checksum_path = get_project_root() / CHECKSUM_FILE
    checksums = load_expected_checksums()
    checksums[filename] = checksum
    with open(checksum_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(filepath: Path, expected_checksum: str) -> bool:
    """Verify the checksum of a downloaded file."""
    actual_checksum = compute_file_hash(filepath)
    return actual_checksum == expected_checksum

def derive_composition_family(composition_str: str) -> str:
    """
    Derive composition family from a composition string using pymatgen.
    Groups by metal/oxide type.
    
    Args:
        composition_str: String representation of composition (e.g., "Fe2O3")
    
    Returns:
        String representing the composition family (e.g., "Oxide_Fe", "Metal_Cu")
    """
    try:
        comp = Composition(composition_str)
        elements = list(comp.elements)
        
        # Determine if it's an oxide (contains O) or other
        if any(el.symbol == 'O' for el in elements):
            # Find the metal element (first non-oxygen)
            metals = [el for el in elements if el.symbol != 'O']
            if metals:
                # Group by the primary metal
                primary_metal = sorted(metals, key=lambda x: comp[x])[0]
                return f"Oxide_{primary_metal.symbol}"
            return "Oxide_Other"
        else:
            # For non-oxides, group by primary element
            primary = sorted(elements, key=lambda x: comp[x])[0]
            return f"Material_{primary.symbol}"
    except Exception as e:
        logger.warning(f"Could not parse composition {composition_str}: {e}")
        return "Unknown"

def download_stratified_sample(output_path: Optional[str] = None) -> Path:
    """
    Download a stratified sample of the OC20 dataset from HuggingFace.
    
    Args:
        output_path: Optional path to save the file. Defaults to OUTPUT_PATH.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        RuntimeError: If download fails or dataset is unavailable.
    """
    if output_path is None:
        output_path = get_project_root() / OUTPUT_PATH
    else:
        output_path = get_project_root() / output_path
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading stratified sample of {DATASET_ID}...")
    logger.info(f"Output path: {output_path}")
    
    try:
        # Load dataset with streaming
        dataset = load_dataset(
            DATASET_ID,
            streaming=True,
            trust_remote_code=True
        )
        
        # Get the split (assuming 'train' or 's2ef' split exists)
        # OC20 experimental might have different splits
        splits = list(dataset.keys())
        if not splits:
            raise RuntimeError(f"No splits found in dataset {DATASET_ID}")
        
        # Use the first available split
        split_name = splits[0]
        logger.info(f"Using split: {split_name}")
        
        split_dataset = dataset[split_name]
        
        # Derive composition family for stratification
        logger.info("Deriving composition families for stratification...")
        
        # Collect all items with their composition families
        items_with_families = []
        for idx, item in enumerate(split_dataset):
            composition_str = item.get('composition', item.get('formula', str(idx)))
            family = derive_composition_family(composition_str)
            items_with_families.append((item, family))
            
            # Log progress every 1000 items
            if (idx + 1) % 1000 == 0:
                logger.info(f"Processed {idx + 1} items...")
            
            # Stop if we have enough items for stratification
            if idx > 10000:  # Limit initial scan for efficiency
                break
        
        # Group items by family
        family_groups: Dict[str, List[Tuple[dict, str]]] = {}
        for item, family in items_with_families:
            if family not in family_groups:
                family_groups[family] = []
            family_groups[family].append((item, family))
        
        logger.info(f"Found {len(family_groups)} composition families")
        
        # Stratified sampling: take proportional samples from each family
        sampled_items = []
        total_target = SAMPLE_SIZE
        
        # Calculate sample size per family
        total_items = len(items_with_families)
        for family, items in family_groups.items():
            family_size = len(items)
            # Proportional allocation
            sample_size = max(1, int((family_size / total_items) * total_target))
            # Take the first sample_size items from this family
            sampled_items.extend([item for item, _ in items[:sample_size]])
        
        logger.info(f"Sampled {len(sampled_items)} items for stratified sample")
        
        if not sampled_items:
            raise RuntimeError("No items sampled - dataset may be empty or inaccessible")
        
        # Write to HDF5 file
        logger.info(f"Writing {len(sampled_items)} items to {output_path}...")
        with h5py.File(output_path, 'w') as hf:
            # Create datasets for each field
            # We'll store the data as JSON strings for simplicity
            # In a real implementation, we'd use more efficient storage
            
            # Determine all unique keys
            all_keys = set()
            for item in sampled_items:
                all_keys.update(item.keys())
            
            # Create datasets
            for key in all_keys:
                data = [str(item.get(key, '')) for item in sampled_items]
                if data:
                    hf.create_dataset(key, data=data)
            
            # Store metadata
            hf.attrs['dataset_id'] = DATASET_ID
            hf.attrs['split'] = split_name
            hf.attrs['sample_size'] = len(sampled_items)
            hf.attrs['composition_families'] = json.dumps(list(family_groups.keys()))
        
        logger.info(f"Successfully downloaded and saved {len(sampled_items)} items")
        
        # Compute and save checksum
        checksum = compute_file_hash(output_path)
        save_checksum(FILE_NAME, checksum)
        logger.info(f"Checksum saved: {checksum}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise RuntimeError(f"Failed to download dataset {DATASET_ID}: {e}")

def verify_downloaded_data(filepath: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify the integrity of the downloaded file.
    
    Args:
        filepath: Path to the downloaded file.
        expected_checksum: Optional expected checksum. If None, loads from checksum file.
    
    Returns:
        True if verification passes, False otherwise.
    
    Raises:
        RuntimeError: If file doesn't exist or checksum verification fails.
    """
    if not filepath.exists():
        raise RuntimeError(f"Downloaded file not found: {filepath}")
    
    actual_checksum = compute_file_hash(filepath)
    
    if expected_checksum is None:
        checksums = load_expected_checksums()
        expected_checksum = checksums.get(FILE_NAME)
    
    if expected_checksum is None:
        logger.warning("No expected checksum found, skipping verification")
        return True
    
    if actual_checksum != expected_checksum:
        raise RuntimeError(
            f"Checksum verification failed for {filepath}. "
            f"Expected: {expected_checksum}, Actual: {actual_checksum}"
        )
    
    logger.info("Checksum verification passed")
    return True

def handle_excluded_datasets(excluded_datasets: List[str]) -> None:
    """
    Log information about excluded datasets.
    
    Args:
        excluded_datasets: List of dataset names that were excluded.
    """
    if excluded_datasets:
        logger.info("Excluded datasets:")
        for ds in excluded_datasets:
            logger.info(f"  - {ds}")

def main():
    """Main entry point for downloading the OC20 dataset."""
    try:
        # Download the stratified sample
        output_path = download_stratified_sample()
        
        # Verify the downloaded data
        verify_downloaded_data(output_path)
        
        logger.info("Data download and verification completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to download data: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
