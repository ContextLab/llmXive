"""
Data download module for MolNet dataset.
Handles fetching, validation, and checksumming of molecular interaction data.
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset
from utils.exceptions import DataError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required fields for the dataset
REQUIRED_FIELDS = ["polymer_smiles", "filler_smiles", "adhesion_energy"]

def compute_file_sha256(file_path: str) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_molnet_data() -> List[Dict[str, Any]]:
    """
    Download the MolNet dataset containing polymer-filler interface data.
    
    Returns:
        List of dictionaries containing polymer_smiles, filler_smiles, 
        and adhesion_energy.
        
    Raises:
        DataError: If the dataset cannot be loaded or required fields are missing.
    """
    try:
        logger.info("Loading MolNet dataset from Hugging Face...")
        # Load the molnet dataset
        dataset = load_dataset('molnet', split='train')
        
        # Convert to list of dicts
        data = dataset.to_list()
        
        if not data:
            raise DataError("E-DATA-001: Downloaded dataset is empty.")
        
        logger.info(f"Successfully downloaded {len(data)} records from MolNet.")
        return data
        
    except Exception as e:
        logger.error(f"Failed to download MolNet dataset: {e}")
        raise DataError(f"E-DATA-001: Failed to download MolNet dataset. {str(e)}")

def validate_fields(data: List[Dict[str, Any]]) -> bool:
    """
    Validate that all records contain required fields.
    
    Args:
        data: List of dictionaries to validate.
        
    Returns:
        True if all required fields are present.
        
    Raises:
        DataError: If any required field is missing.
    """
    missing_fields = set()
    for i, record in enumerate(data):
        for field in REQUIRED_FIELDS:
            if field not in record or record[field] is None:
                missing_fields.add(field)
    
    if missing_fields:
        raise DataError(
            f"E-DATA-001: Missing required fields in dataset: {missing_fields}"
        )
    
    logger.info("All required fields validated successfully.")
    return True

def save_data(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: List of dictionaries to save.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Data saved to {output_path}")

def save_checksums(checksums: Dict[str, str], output_path: str) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary mapping filenames to their SHA256 hashes.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Checksums saved to {output_path}")

def main():
    """Main entry point for data download and validation."""
    # Define paths
    project_root = Path(__file__).resolve().parents[2]
    raw_data_dir = project_root / "data" / "raw"
    output_file = raw_data_dir / "molnet_data.json"
    checksum_file = raw_data_dir / "checksums.json"
    
    # Ensure directory exists
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download data
        data = download_molnet_data()
        
        # Validate fields
        validate_fields(data)
        
        # Save data
        save_data(data, str(output_file))
        
        # Compute and save checksum
        file_hash = compute_file_sha256(str(output_file))
        checksums = {
            "molnet_data.json": file_hash
        }
        save_checksums(checksums, str(checksum_file))
        
        logger.info("Data download and validation completed successfully.")
        
    except DataError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
