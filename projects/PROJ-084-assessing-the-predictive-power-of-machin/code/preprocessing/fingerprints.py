"""
Generate ECFP4 and MACCS fingerprints for chemical structures.

Functions:
- generate_ecfp4: Generate ECFP4 fingerprint (2048 bits)
- generate_maccs: Generate MACCS fingerprint (167 bits)
- generate_fingerprints_batch: Apply to a DataFrame
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/fingerprint.log')
    ]
)
logger = logging.getLogger(__name__)

def generate_ecfp4(smiles: str, radius: int = 2, n_bits: int = 2048) -> Optional[List[int]]:
    """
    Generate ECFP4 fingerprint for a SMILES string.
    
    Args:
        smiles: SMILES string
        radius: ECFP radius (2 for ECFP4)
        n_bits: Number of bits in fingerprint
    
    Returns:
        List of integers (0 or 1) representing the fingerprint
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros((n_bits,), dtype=int)
        Chem.DataStructs.ConvertToNumpyArray(fp, arr)
        return arr.tolist()
    except Exception as e:
        logger.debug(f"Failed to generate ECFP4 for {smiles}: {e}")
        return None

def generate_maccs(smiles: str) -> Optional[List[int]]:
    """
    Generate MACCS fingerprint for a SMILES string.
    
    Args:
        smiles: SMILES string
    
    Returns:
        List of integers (0 or 1) representing the fingerprint (167 bits)
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        fp = MACCSkeys.GenMACCSKeys(mol)
        arr = np.zeros((167,), dtype=int)
        Chem.DataStructs.ConvertToNumpyArray(fp, arr)
        return arr.tolist()
    except Exception as e:
        logger.debug(f"Failed to generate MACCS for {smiles}: {e}")
        return None

def generate_fingerprints_batch(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """
    Generate ECFP4 and MACCS fingerprints for a DataFrame of SMILES.
    
    Args:
        df: DataFrame with a 'smiles' column
        smiles_col: Name of the SMILES column
    
    Returns:
        DataFrame with additional columns: fingerprint_ecfp, fingerprint_maccs
    """
    logger.info(f"Generating fingerprints for {len(df)} molecules...")
    
    ecfp_list = []
    maccs_list = []
    valid_indices = []
    
    for idx, smiles in enumerate(df[smiles_col]):
        ecfp = generate_ecfp4(smiles)
        maccs = generate_maccs(smiles)
        
        if ecfp is not None and maccs is not None:
            ecfp_list.append(ecfp)
            maccs_list.append(maccs)
            valid_indices.append(idx)
        else:
            logger.warning(f"Failed to generate fingerprints for row {idx}: {smiles}")
    
    logger.info(f"Generated fingerprints for {len(valid_indices)} molecules")
    
    if len(valid_indices) == 0:
        raise ValueError("No valid fingerprints generated")
    
    # Filter DataFrame to only valid rows
    df_valid = df.iloc[valid_indices].copy()
    
    # Add fingerprint columns
    df_valid['fingerprint_ecfp'] = ecfp_list
    df_valid['fingerprint_maccs'] = maccs_list
    
    return df_valid

def main():
    """Entry point for fingerprint generation script."""
    logger.info("Starting fingerprint generation (T016)...")
    
    try:
        # This is a helper function, not a full script
        # The full pipeline is run by ingest.py
        logger.info("Fingerprint functions ready. Run ingest.py for full pipeline.")
    except Exception as e:
        logger.error(f"Fingerprint generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
