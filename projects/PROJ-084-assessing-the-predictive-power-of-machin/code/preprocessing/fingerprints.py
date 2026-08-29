from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import DataStructs
import numpy as np
from typing import Union, List
import pandas as pd
import logging
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def generate_ecfp4(smiles: str, n_bits: int = 2048) -> np.ndarray:
    """Generate ECFP4 fingerprint for a SMILES string.
    
    Args:
        smiles: SMILES string representing a molecule.
        n_bits: Number of bits in the fingerprint (default 2048).
        
    Returns:
        Numpy array of uint8 (0 or 1) of length n_bits.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Failed to parse SMILES: {smiles}. Returning zero vector.")
        return np.zeros(n_bits, dtype=np.uint8)
    
    # Morgan fingerprint with radius 2 corresponds to ECFP4
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.uint8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def generate_maccs(smiles: str) -> np.ndarray:
    """Generate MACCS keys fingerprint for a SMILES string.
    
    Args:
        smiles: SMILES string representing a molecule.
        
    Returns:
        Numpy array of uint8 (0 or 1) of length 167.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Failed to parse SMILES: {smiles}. Returning zero vector.")
        return np.zeros(167, dtype=np.uint8)
    
    fp = MACCSkeys.GenMACCSKeys(mol)
    arr = np.zeros((167,), dtype=np.uint8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def generate_fingerprints_batch(df: pd.DataFrame, smiles_col: str = "canonical_smiles") -> pd.DataFrame:
    """Generate ECFP4 and MACCS fingerprints for a batch of reactions.
    
    This function iterates over the DataFrame, applying fingerprint generation
    to each SMILES string. It logs progress and handles invalid SMILES gracefully
    by returning zero vectors (as per FR-003).
    
    Args:
        df: Pandas DataFrame containing a column with SMILES strings.
        smiles_col: Name of the column containing SMILES strings (default: "canonical_smiles").
        
    Returns:
        DataFrame with two new columns: 'ecfp4' (list of int) and 'maccs' (list of int).
        
    Raises:
        ValueError: If the specified smiles_col does not exist in the DataFrame.
    """
    if smiles_col not in df.columns:
        raise ValueError(f"Column '{smiles_col}' not found in DataFrame. Available columns: {list(df.columns)}")
    
    logger.info(f"Starting fingerprint generation for {len(df)} rows on column '{smiles_col}'...")
    
    # Apply functions and convert list outputs to lists for Parquet compatibility
    # We store them as lists of integers to ensure Parquet serialization works correctly
    ecfp4_list = []
    maccs_list = []
    
    for idx, smiles in enumerate(df[smiles_col]):
        if idx % 10000 == 0 and idx > 0:
            logger.info(f"Processed {idx}/{len(df)} rows...")
        
        ecfp4_vec = generate_ecfp4(smiles)
        maccs_vec = generate_maccs(smiles)
        
        ecfp4_list.append(ecfp4_vec.tolist())
        maccs_list.append(maccs_vec.tolist())
    
    df['ecfp4'] = ecfp4_list
    df['maccs'] = maccs_list
    
    logger.info("Fingerprint generation completed.")
    return df

def main():
    """Main entry point for running the fingerprint generation pipeline.
    
    This script is designed to be run as part of the ingestion pipeline (T017).
    It expects the cleaned reactions data to be available at the configured path.
    For demonstration/testing purposes, it can also run on a small subset if
    the full file is not yet available (though the real pipeline requires the full file).
    """
    from config import DATA_PROCESSED_DIR, DATA_RAW_DIR
    
    input_path = DATA_PROCESSED_DIR / "cleaned_reactions.parquet"
    output_path = DATA_PROCESSED_DIR / "cleaned_reactions_fingerprints.parquet"
    
    if not input_path.exists():
        # Check if raw data exists as a fallback for testing
        raw_path = DATA_RAW_DIR / "uspto_raw.parquet"
        if raw_path.exists():
            logger.warning(f"Input file {input_path} not found. Attempting to use {raw_path} for testing.")
            input_path = raw_path
            output_path = DATA_PROCESSED_DIR / "uspto_fingerprints.parquet"
        else:
            logger.error(f"Neither {input_path} nor {raw_path} found. Cannot proceed.")
            logger.error("Please ensure T017 (ingest.py) or T019 (download.py) has been run successfully.")
            sys.exit(1)
    
    logger.info(f"Loading data from {input_path}...")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    # Determine the correct SMILES column name
    smiles_col = "canonical_smiles"
    if smiles_col not in df.columns:
        # Fallback to common alternatives
        for alt in ["smiles", "reaction_smiles", "reactant_smiles"]:
            if alt in df.columns:
                smiles_col = alt
                logger.info(f"Using alternative SMILES column: {smiles_col}")
                break
        else:
            logger.error(f"Could not find a SMILES column. Available: {list(df.columns)}")
            sys.exit(1)
    
    # Generate fingerprints
    df_processed = generate_fingerprints_batch(df, smiles_col=smiles_col)
    
    # Save results
    logger.info(f"Saving results to {output_path}...")
    try:
        df_processed.to_parquet(output_path, index=False)
        logger.info(f"Successfully saved {len(df_processed)} rows to {output_path}")
        
        # Verify dimensions
        sample_ecfp4 = df_processed.iloc[0]['ecfp4']
        sample_maccs = df_processed.iloc[0]['maccs']
        logger.info(f"Sample ECFP4 dimension: {len(sample_ecfp4)} (expected 2048)")
        logger.info(f"Sample MACCS dimension: {len(sample_maccs)} (expected 167)")
        
    except Exception as e:
        logger.error(f"Failed to save parquet file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()