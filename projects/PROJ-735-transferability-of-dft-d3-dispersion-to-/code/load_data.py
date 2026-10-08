import hashlib
import os
import zipfile
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import json
import re

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

def _validate_xyz_content(content: str) -> bool:
    """
    Validate XYZ file content.
    XYZ format:
      Line 1: Number of atoms
      Line 2: Comment
      Lines 3..N+2: Element X Y Z (must be numeric)
    
    Returns True if valid, raises ValueError if invalid.
    """
    lines = content.strip().split('\n')
    if len(lines) < 3:
        raise ValueError("XYZ file must have at least 3 lines (count, comment, and at least one atom)")
    
    try:
        num_atoms = int(lines[0].strip())
    except ValueError:
        raise ValueError(f"First line of XYZ must be an integer (atom count), got: '{lines[0].strip()}'")
    
    if len(lines) != num_atoms + 2:
        raise ValueError(f"XYZ file atom count mismatch: header says {num_atoms}, but found {len(lines) - 2} atom lines")
    
    # Validate atom lines
    coord_pattern = re.compile(r'^[A-Za-z]{1,3}\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)$')
    for i, line in enumerate(lines[2:], start=3):
        line = line.strip()
        if not line:
            continue
        if not coord_pattern.match(line):
            raise ValueError(f"Invalid coordinate format on line {i}: '{line}'. Expected 'Element X Y Z' with numeric coordinates.")
    
    return True

def _validate_csv_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that a DataFrame contains all required columns.
    Raises ValueError if any required column is missing.
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")
    return True

def load_synthetic_dataset(zip_path: Path) -> Tuple[List[dict], pd.DataFrame]:
    """
    Load the synthetic dataset from the zip file.
    Validates XYZ content and CSV columns.
    
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
            elif file_name.endswith(".xyz"):
                # Validate XYZ content
                xyz_content = zip_ref.read(file_name).decode('utf-8')
                _validate_xyz_content(xyz_content)
                logger.info(f"Validated XYZ file: {file_name}")
    
    # Load bulk properties CSV (assumed to be in the same directory)
    csv_path = zip_path.parent / "experimental_bulk_properties.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Bulk properties CSV not found: {csv_path}")
    
    df_bulk = pd.read_csv(csv_path)
    
    # Validate CSV columns (assuming required columns for bulk properties)
    # Based on T030, we expect columns like 'pair_id', 'density', 'viscosity'
    required_bulk_cols = ['pair_id', 'density', 'viscosity']
    _validate_csv_columns(df_bulk, required_bulk_cols)
    logger.info(f"Validated bulk properties CSV with columns: {list(df_bulk.columns)}")
    
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
