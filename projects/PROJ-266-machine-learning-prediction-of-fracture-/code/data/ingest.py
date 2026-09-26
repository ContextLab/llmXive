import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import argparse
import sys

from code.utils.logger import get_logger

logger = get_logger("ingest")


def load_csv(csv_path: str) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    path = Path(csv_path)
    if not path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    logger.info(f"Loading CSV from {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows")
    return df


def load_metadata(metadata_path: str) -> List[Dict[str, Any]]:
    """Load metadata from a JSON file."""
    path = Path(metadata_path)
    if not path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    logger.info(f"Loading metadata from {metadata_path}")
    with open(path, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} metadata entries")
    return data


def validate_kic_values(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that all K_IC values are present and numeric.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    if 'k_ic' not in df.columns:
        errors.append("Column 'k_ic' is missing from the dataset.")
        return False, errors
    
    missing_count = df['k_ic'].isna().sum()
    if missing_count > 0:
        missing_indices = df[df['k_ic'].isna()].index.tolist()
        errors.append(f"Found {missing_count} missing K_IC values at indices: {missing_indices}")
    
    # Check for non-numeric values
    non_numeric = df[~df['k_ic'].apply(lambda x: isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).replace('-', '', 1).isdigit()))]
    if not non_numeric.empty:
        errors.append(f"Found {len(non_numeric)} non-numeric K_IC values.")
    
    is_valid = len(errors) == 0
    if not is_valid:
        for err in errors:
            logger.error(err)
    else:
        logger.info("K_IC validation passed.")
    
    return is_valid, errors


def validate_image_paths(df: pd.DataFrame, base_dir: Optional[str] = None) -> Tuple[bool, List[str]]:
    """Validate that image paths exist."""
    errors = []
    if 'image_path' not in df.columns:
        errors.append("Column 'image_path' is missing.")
        return False, errors
    
    missing_paths = []
    for idx, row in df.iterrows():
        path_str = row['image_path']
        full_path = Path(base_dir) / path_str if base_dir else Path(path_str)
        if not full_path.exists():
            missing_paths.append(str(full_path))
    
    if missing_paths:
        errors.append(f"Found {len(missing_paths)} missing image files.")
        logger.warning(f"Missing images: {missing_paths[:5]}...") # Log first 5
    
    return len(errors) == 0, errors


def validate_metadata_structure(metadata: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate the structure of the metadata list."""
    errors = []
    required_keys = {'image_id', 'image_path', 'alloy_family', 'k_ic'}
    
    for i, entry in enumerate(metadata):
        if not isinstance(entry, dict):
            errors.append(f"Entry {i} is not a dictionary.")
            continue
        
        missing = required_keys - set(entry.keys())
        if missing:
            errors.append(f"Entry {i} missing keys: {missing}")
    
    return len(errors) == 0, errors


def compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_checksum(metadata_file: str, checksum_file: str) -> Tuple[bool, str]:
    """Validate the checksum of a metadata file against a stored checksum."""
    if not os.path.exists(metadata_file):
        return False, f"Metadata file not found: {metadata_file}"
    if not os.path.exists(checksum_file):
        return False, f"Checksum file not found: {checksum_file}"
    
    with open(checksum_file, 'r') as f:
        checksum_data = json.load(f)
    
    expected_hash = checksum_data.get('sha256')
    if not expected_hash:
        return False, "Invalid checksum file format."
    
    actual_hash = compute_file_checksum(metadata_file)
    
    if actual_hash == expected_hash:
        logger.info("Checksum validation passed.")
        return True, "Checksum matches."
    else:
        error_msg = f"Checksum mismatch. Expected: {expected_hash}, Got: {actual_hash}"
        logger.error(error_msg)
        return False, error_msg


def generate_checksum_manifest(metadata_file: str, output_file: str) -> None:
    """Generate a manifest file with the checksum of the metadata file."""
    checksum = compute_file_checksum(metadata_file)
    manifest = {
        "metadata_file": metadata_file,
        "sha256": checksum,
        "generated_at": str(pd.Timestamp.now())
    }
    
    with open(output_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Checksum manifest written to {output_file}")


def save_checksum_manifest(checksum_data: Dict, output_file: str) -> None:
    """Save a checksum manifest to a file."""
    with open(output_file, 'w') as f:
        json.dump(checksum_data, f, indent=2)
    logger.info(f"Saved checksum manifest to {output_file}")


def load_checksum_manifest(manifest_file: str) -> Dict:
    """Load a checksum manifest from a file."""
    with open(manifest_file, 'r') as f:
        return json.load(f)


def validate_dataset_integrity(metadata_file: str, checksum_file: str) -> bool:
    """Perform full dataset integrity check."""
    valid, msg = validate_checksum(metadata_file, checksum_file)
    if not valid:
        logger.error(f"Integrity check failed: {msg}")
        return False
    
    try:
        df = load_csv(metadata_file) # Assuming metadata is CSV or JSON converted
        # If metadata is JSON, load_metadata would be used instead
        is_valid_kic, kic_errors = validate_kic_values(df)
        if not is_valid_kic:
            logger.error(f"K_IC validation failed: {kic_errors}")
            return False
        
        logger.info("Dataset integrity check passed.")
        return True
    except Exception as e:
        logger.error(f"Error during integrity check: {e}")
        return False


def main():
    """
    Main entry point for validation scripts.
    Usage: python code/data/ingest.py --csv <path_to_csv>
    """
    parser = argparse.ArgumentParser(description="Validate dataset ingestion")
    parser.add_argument('--csv', type=str, required=True, help='Path to the CSV file to validate')
    args = parser.parse_args()
    
    logger.info(f"Starting validation for {args.csv}")
    
    try:
        df = load_csv(args.csv)
        is_valid, errors = validate_kic_values(df)
        
        if not is_valid:
            logger.error("Validation failed due to missing or invalid K_IC values.")
            sys.exit(1)
        
        logger.info("Validation successful.")
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()