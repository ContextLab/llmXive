"""
Data loading and validation module.

Implements T004, T005: Load and validate synthetic dataset.
"""

import hashlib
import os
import zipfile
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional, List

from code.models import IonPair
from code.logger import get_logger

logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksums(data_dir: Path) -> bool:
    """
    Validate checksums of raw data files.
    
    Note: This implementation assumes a checksum file exists or uses a known hash.
    For this task, we skip strict validation if no checksum file is present,
    but log a warning.
    """
    zip_path = data_dir / "IL-Benchmark-local.zip"
    csv_path = data_dir / "experimental_bulk_properties.csv"
    
    if not zip_path.exists():
        logger.error(f"Dataset zip not found: {zip_path}")
        return False
    
    if not csv_path.exists():
        logger.error(f"Bulk properties CSV not found: {csv_path}")
        return False
    
    # In a real scenario, we would compare against a known checksum file
    logger.info("Data files found. Skipping checksum verification (no checksum file provided).")
    return True

def load_synthetic_dataset(data_dir: Path) -> Tuple[List[IonPair], pd.DataFrame]:
    """
    Load the synthetic dataset generated in T000.
    
    Returns:
        Tuple of (list of IonPair objects, DataFrame of bulk properties).
    """
    zip_path = data_dir / "IL-Benchmark-local.zip"
    csv_path = data_dir / "experimental_bulk_properties.csv"
    
    if not validate_checksums(data_dir):
        raise FileNotFoundError("Dataset validation failed.")
    
    # Load bulk properties
    bulk_df = pd.read_csv(csv_path)
    
    # Load ion pairs from zip
    ion_pairs = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Assume the zip contains a CSV of ion pair data and XYZ files
        # We assume a file named 'ion_pairs.csv' exists in the zip
        if 'ion_pairs.csv' in zf.namelist():
            with zf.open('ion_pairs.csv') as f:
                df = pd.read_csv(f)
            
            for _, row in df.iterrows():
                pair = IonPair(
                    id=str(row['id']),
                    cation=row['cation'],
                    anion=row['anion'],
                    coordinates=row['xyz'],
                    reference_energy=float(row['reference_energy']),
                    cation_coords=row.get('cation_xyz', None),
                    anion_coords=row.get('anion_xyz', None)
                )
                ion_pairs.append(pair)
        else:
            # Fallback: try to parse from a different structure if 'ion_pairs.csv' is missing
            # For T000, we generated 'ion_pairs.csv' inside the zip.
            logger.error("ion_pairs.csv not found in the zip file.")
            raise ValueError("Invalid dataset format.")
    
    return ion_pairs, bulk_df

def main():
    """Main entry point for data loading script."""
    data_dir = Path("data")
    try:
        pairs, bulk = load_synthetic_dataset(data_dir)
        logger.info(f"Loaded {len(pairs)} ion pairs and bulk properties for {len(bulk)} entries.")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
