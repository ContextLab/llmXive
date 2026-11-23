"""
Extended data loading utilities for molecular packing efficiency pipeline.

This module provides additional utilities for loading, validating, and
preprocessing CIF data and derived datasets.

Functions:
    load_cod_sample: Load a sample of COD data for testing.
    validate_smiles: Validate SMILES strings using RDKit.
    filter_by_atom_count: Filter dataset by atom count.
    merge_with_metadata: Merge dataset with external metadata.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Any

import pandas as pd
import numpy as np

from rdkit import Chem
from rdkit.Chem import Descriptors

from cif_loader import parse_cif_file, create_dataset_dataframe, BONDI_RADII
from utils import fix_seed, setup_logging
from error_handling import CIFParseError, handle_corrupt_cif

logger = logging.getLogger(__name__)

def load_cod_sample(
    cod_dir: str,
    n_samples: int = 100,
    max_atom_count: int = 50
) -> pd.DataFrame:
    """
    Load a sample of COD data for testing and development.
    
    Args:
        cod_dir: Directory containing downloaded CIF files.
        n_samples: Number of samples to load.
        max_atom_count: Maximum number of non-H atoms allowed.
        
    Returns:
        DataFrame with parsed CIF data.
    """
    fix_seed(42)
    cif_data_list = []
    
    for data in load_cif_batch(cod_dir, max_files=n_samples * 2):
        # Count non-H atoms
        non_h_count = sum(1 for atom in data['atoms'] if atom['symbol'] != 'H')
        
        if non_h_count <= max_atom_count:
            cif_data_list.append(data)
            if len(cif_data_list) >= n_samples:
                break
                
    return create_dataset_dataframe(cif_data_list)

def validate_smiles(smiles: str) -> bool:
    """
    Validate a SMILES string using RDKit.
    
    Args:
        smiles: SMILES string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False
        
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def filter_by_atom_count(
    df: pd.DataFrame,
    max_atoms: int = 50,
    min_atoms: int = 1
) -> pd.DataFrame:
    """
    Filter dataset by atom count.
    
    Args:
        df: Input DataFrame.
        max_atoms: Maximum number of atoms.
        min_atoms: Minimum number of atoms.
        
    Returns:
        Filtered DataFrame.
    """
    if 'atom_count' not in df.columns:
        logger.warning("Column 'atom_count' not found in DataFrame")
        return df
        
    return df[
        (df['atom_count'] >= min_atoms) & 
        (df['atom_count'] <= max_atoms)
    ].reset_index(drop=True)

def load_cif_batch(
    cif_dir: str,
    max_files: Optional[int] = None,
    extensions: List[str] = ['.cif']
) -> Any:
    """
    Wrapper to import load_cif_batch from cif_loader.
    
    This is a re-export to maintain a consistent API surface.
    """
    from cif_loader import load_cif_batch as _load_batch
    return _load_batch(cif_dir, max_files, extensions)
