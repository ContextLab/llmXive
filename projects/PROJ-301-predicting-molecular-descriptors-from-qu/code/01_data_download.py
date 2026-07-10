import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Import from local project modules
from config import set_seeds
from utils.logger import get_logger, configure_logging_for_pipeline
from utils.parsers import validate_molecule, parse_xyz_to_mol
from utils.memory_monitor import get_memory_usage_gb, check_memory_limit

# Configure logger
logger = get_logger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
QM9_REQUIRED_COLUMNS = [
    'mu',  # Dipole moment
    'alpha',
    'homo',  # HOMO
    'lumo',  # LUMO
    'gap',
    'r2',
    'zpve',
    'u0',
    'u298',
    'h298',
    'g298',
    'c_v',
    'u0_atom',
    'u298_atom',
    'h298_atom',
    'g298_atom',
    'n_atoms',
    'n_carbon',
    'n_hydrogen',
    'n_nitrogen',
    'n_oxygen',
    'n_fluorine',
    'coords'  # 3D coordinates
]

def compute_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_data_integrity(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame contains required DFT columns and valid 3D coordinates.
    Returns True if valid, False otherwise.
    """
    # Check for required columns
    missing_cols = [col for col in QM9_REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False

    # Check for valid geometry (coords column must not be null)
    if df['coords'].isnull().any():
        logger.warning(f"Found {df['coords'].isnull().sum()} rows with null coordinates")
        return False

    # Check for valid DFT values (no NaN in key properties)
    key_dft_cols = ['mu', 'homo', 'lumo', 'alpha']
    for col in key_dft_cols:
        if df[col].isnull().any():
            logger.warning(f"Found {df[col].isnull().sum()} NaN values in {col}")
            return False

    return True

def download_qm9_dataset(output_dir: str = "data/raw") -> str:
    """
    Download QM9 dataset from HuggingFace (lisn/QM9) and save to parquet.
    Returns path to the saved file.
    """
    from huggingface_hub import hf_hub_download
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "qm9_full.parquet")
    
    if os.path.exists(output_path):
        logger.info(f"Dataset already exists at {output_path}")
        return output_path

    logger.info("Downloading QM9 dataset from HuggingFace (lisn/QM9)...")
    try:
        # Download the main dataset file from HuggingFace
        local_path = hf_hub_download(
            repo_id="lisn/QM9",
            filename="qm9.parquet",
            repo_type="dataset"
        )
        
        # Load and verify
        df = pd.read_parquet(local_path)
        
        if not validate_data_integrity(df):
            logger.error("Downloaded data failed integrity check")
            raise ValueError("Data integrity check failed")
        
        # Save to project location
        df.to_parquet(output_path, index=False)
        
        # Compute and save checksum
        checksum = compute_file_checksum(output_path)
        checksum_path = "data/checksums.json"
        os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
        
        checksum_data = {"qm9_full.parquet": checksum}
        if os.path.exists(checksum_path):
            with open(checksum_path, 'r') as f:
                existing = json.load(f)
            existing.update(checksum_data)
        else:
            existing = checksum_data
            
        with open(checksum_path, 'w') as f:
            json.dump(existing, f, indent=2)
            
        logger.info(f"Dataset saved to {output_path} with checksum {checksum}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def parse_and_validate(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Parse the downloaded QM9 dataset, validate molecule structures,
    filter out rows with missing DFT labels or invalid geometry,
    and save the cleaned dataset.
    """
    logger.info(f"Loading dataset from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load data
    df = pd.read_parquet(input_path)
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} molecules")
    
    # Memory check
    mem_gb = get_memory_usage_gb()
    if mem_gb > MEMORY_LIMIT_GB:
        logger.warning(f"Memory usage ({mem_gb:.2f} GB) exceeds limit. Starting cleanup.")
    
    # 1. Drop rows with missing DFT labels
    key_dft_cols = ['mu', 'homo', 'lumo', 'alpha']
    mask_dft = df[key_dft_cols].notna().all(axis=1)
    df = df[mask_dft]
    logger.info(f"After DFT label validation: {len(df)} molecules (dropped {initial_count - len(df)})")
    
    # 2. Validate geometry and 3D coordinates
    # The 'coords' column in QM9 parquet is typically a list of [x, y, z] for each atom
    # We need to ensure it's a valid numpy array and has correct shape
    valid_indices = []
    
    for idx, row in df.iterrows():
        try:
            coords = row['coords']
            if coords is None or pd.isna(coords):
                continue
            
            # Convert to numpy array if needed
            if isinstance(coords, list):
                coords_arr = np.array(coords)
            elif isinstance(coords, np.ndarray):
                coords_arr = coords
            else:
                # Try to parse if it's a string representation
                coords_arr = np.fromstring(coords.strip('[]'), sep=' ').reshape(-1, 3)
            
            # Validate shape (should be N_atoms x 3)
            n_atoms = row.get('n_atoms', 0)
            if coords_arr.shape[0] != n_atoms or coords_arr.shape[1] != 3:
                logger.debug(f"Molecule {idx}: Invalid coordinate shape {coords_arr.shape} vs expected {n_atoms}x3")
                continue
            
            # Optional: Validate using RDKit if SMILES is available
            if 'smiles' in row.index and pd.notna(row['smiles']):
                mol = Chem.MolFromSmiles(row['smiles'])
                if mol is None:
                    logger.debug(f"Molecule {idx}: Invalid SMILES")
                    continue
                
                # Validate atom count matches
                if mol.GetNumAtoms() != n_atoms:
                    logger.debug(f"Molecule {idx}: Atom count mismatch (SMILES: {mol.GetNumAtoms()}, Data: {n_atoms})")
                    continue
            
            valid_indices.append(idx)
            
        except Exception as e:
            logger.debug(f"Molecule {idx} validation failed: {e}")
            continue
    
    logger.info(f"Validating {len(valid_indices)} molecules...")
    df_clean = df.iloc[valid_indices].reset_index(drop=True)
    
    final_count = len(df_clean)
    logger.info(f"Final cleaned dataset: {final_count} molecules (dropped {initial_count - final_count} total)")
    
    if final_count == 0:
        raise ValueError("No valid molecules found after filtering")
    
    # Save cleaned dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_clean.to_parquet(output_path, index=False)
    logger.info(f"Cleaned dataset saved to {output_path}")
    
    return df_clean

def main():
    """Main entry point for the data download and parsing pipeline."""
    set_seeds()
    configure_logging_for_pipeline()
    
    # Paths
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    
    input_file = os.path.join(raw_dir, "qm9_full.parquet")
    output_file = os.path.join(processed_dir, "molecules_cleaned.parquet")
    
    # Step 1: Download if not exists (T009 logic)
    if not os.path.exists(input_file):
        logger.info("Raw data not found. Downloading...")
        try:
            download_qm9_dataset(raw_dir)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return 1
    
    # Step 2: Parse and Validate (T010 logic)
    try:
        logger.info("Starting parse and validate phase...")
        df_clean = parse_and_validate(input_file, output_file)
        logger.info("Parse and validate completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Parse and validate failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
