import hashlib
import os
import zipfile
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import json

from logger import get_logger

logger = get_logger(__name__)

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksums(checksums: Dict[str, str]) -> bool:
    """Validate files against provided checksums."""
    all_valid = True
    for filepath, expected_hash in checksums.items():
        p = Path(filepath)
        if not p.exists():
            logger.error(f"File missing: {filepath}")
            all_valid = False
            continue
        
        actual_hash = calculate_sha256(p)
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {filepath}: expected {expected_hash}, got {actual_hash}")
            all_valid = False
        else:
            logger.info(f"Checksum valid: {filepath}")
    return all_valid

def load_synthetic_dataset(zip_path: Path) -> Tuple[List[dict], pd.DataFrame]:
    """
    Load the synthetic dataset from the zip file.
    Returns:
      - List of dicts with pair_id and reference_energy
      - DataFrame with bulk properties
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"Dataset zip not found: {zip_path}")
    
    pairs_data = []
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            if file_name.endswith("_meta.json"):
                content = zip_ref.read(file_name).decode('utf-8')
                data = json.loads(content)
                pairs_data.append(data)
    
    # Load bulk properties CSV (assumed to be in the same directory)
    csv_path = zip_path.parent / "experimental_bulk_properties.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Bulk properties CSV not found: {csv_path}")
    
    df_bulk = pd.read_csv(csv_path)
    
    return pairs_data, df_bulk

def main():
    # Example usage
    zip_path = Path("data/IL-Benchmark-local.zip")
    try:
        pairs, bulk = load_synthetic_dataset(zip_path)
        print(f"Loaded {len(pairs)} pairs and bulk properties shape {bulk.shape}")
    except Exception as e:
        print(f"Error loading data: {e}")

if __name__ == "__main__":
    main()