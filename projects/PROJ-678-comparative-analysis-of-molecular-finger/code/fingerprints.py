import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import DataStructs
import logging
import pickle
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd

from utils import setup_logging, init_random_seed, get_logger
from constants import MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS

def generate_morgan_fingerprint(smiles: str, radius: int = MORGAN_RADIUS, n_bits: int = MORGAN_BITS):
    """Generate Morgan fingerprint for a SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    return fp

def generate_maccs_fingerprint(smiles: str):
    """Generate MACCS fingerprint for a SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = MACCSkeys.GenMACCSKeys(mol)
    return fp

def calculate_tanimoto_similarity(fp1, fp2) -> float:
    """Calculate Tanimoto similarity between two fingerprints."""
    if fp1 is None or fp2 is None:
        return 0.0
    return DataStructs.TanimotoSimilarity(fp1, fp2)

def get_fingerprint_bit_info(fp):
    """Get bit information for a fingerprint."""
    # Returns a list of on-bit indices
    return fp.GetOnBits()

def generate_fingerprints_batch(
    smiles_list: List[str],
    fp_type: str = "morgan",
    batch_size: int = 500
) -> Tuple[np.ndarray, List[Optional[str]]]:
    """
    Generate fingerprints for a batch of SMILES strings.

    Args:
        smiles_list: List of SMILES strings.
        fp_type: Type of fingerprint ('morgan' or 'maccs').
        batch_size: Batch size for processing.

    Returns:
        Tuple of (numpy array of fingerprints, list of failed SMILES).
    """
    logger = get_logger(__name__)
    logger.info(f"Generating {fp_type} fingerprints for {len(smiles_list)} compounds")

    fps = []
    failed_smiles = []

    for i in range(0, len(smiles_list), batch_size):
        batch = smiles_list[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} compounds")

        for smiles in batch:
            if fp_type == "morgan":
                fp = generate_morgan_fingerprint(smiles)
            elif fp_type == "maccs":
                fp = generate_maccs_fingerprint(smiles)
            else:
                raise ValueError(f"Unknown fingerprint type: {fp_type}")

            if fp is not None:
                # Convert to numpy array
                arr = np.zeros((1,), dtype=np.int8)
                DataStructs.ConvertToNumpyArray(fp, arr)
                fps.append(arr)
            else:
                failed_smiles.append(smiles)

    if len(failed_smiles) > 0:
        logger.warning(f"Failed to generate fingerprints for {len(failed_smiles)} compounds")

    logger.info(f"Successfully generated {len(fps)} fingerprints")
    return np.array(fps), failed_smiles

def load_compounds(input_path: str) -> pd.DataFrame:
    """Load compounds from a CSV file."""
    logger = get_logger(__name__)
    logger.info(f"Loading compounds from {input_path}")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} compounds")
    return df

def generate_all_fingerprints(
    input_csv: str,
    output_dir: str,
    morgan_radius: int = MORGAN_RADIUS,
    morgan_bits: int = MORGAN_BITS,
    maccs_bits: int = MACCS_BITS,
    batch_size: int = 500
) -> None:
    """
    Generate both Morgan and MACCS fingerprints for all compounds in the input CSV.
    Saves results as pickle files in the output directory.

    Args:
        input_csv: Path to the input CSV file containing SMILES.
        output_dir: Directory to save output files.
        morgan_radius: Radius for Morgan fingerprint.
        morgan_bits: Number of bits for Morgan fingerprint.
        maccs_bits: Number of bits for MACCS fingerprint.
        batch_size: Batch size for processing.
    """
    logger = get_logger(__name__)
    setup_logging()
    init_random_seed()
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load compounds
    df = load_compounds(input_csv)
    
    if 'smiles' not in df.columns:
        raise ValueError("Input CSV must contain a 'smiles' column")
    
    smiles_list = df['smiles'].tolist()
    logger.info(f"Processing {len(smiles_list)} compounds")
    
    # Generate Morgan fingerprints
    logger.info("Generating Morgan fingerprints...")
    morgan_fps, morgan_failed = generate_fingerprints_batch(
        smiles_list, 
        fp_type="morgan", 
        batch_size=batch_size
    )
    
    # Generate MACCS fingerprints
    logger.info("Generating MACCS fingerprints...")
    maccs_fps, maccs_failed = generate_fingerprints_batch(
        smiles_list, 
        fp_type="maccs", 
        batch_size=batch_size
    )
    
    # Save Morgan fingerprints
    morgan_output = Path(output_dir) / "fingerprints_morgan.pkl"
    with open(morgan_output, 'wb') as f:
        pickle.dump({
            'fingerprints': morgan_fps,
            'smiles': [s for s, fp in zip(smiles_list, morgan_fps) if fp is not None],
            'failed_smiles': morgan_failed,
            'params': {
                'type': 'morgan',
                'radius': morgan_radius,
                'n_bits': morgan_bits
            }
        }, f)
    logger.info(f"Saved Morgan fingerprints to {morgan_output}")
    
    # Save MACCS fingerprints
    maccs_output = Path(output_dir) / "fingerprints_maccs.pkl"
    with open(maccs_output, 'wb') as f:
        pickle.dump({
            'fingerprints': maccs_fps,
            'smiles': [s for s, fp in zip(smiles_list, maccs_fps) if fp is not None],
            'failed_smiles': maccs_failed,
            'params': {
                'type': 'maccs',
                'n_bits': maccs_bits
            }
        }, f)
    logger.info(f"Saved MACCS fingerprints to {maccs_output}")
    
    # Summary
    logger.info("Fingerprint generation complete:")
    logger.info(f"  Morgan: {len(morgan_fps)} successful, {len(morgan_failed)} failed")
    logger.info(f"  MACCS: {len(maccs_fps)} successful, {len(maccs_failed)} failed")

def main():
    """Main entry point for fingerprint generation."""
    setup_logging()
    init_random_seed()
    logger = get_logger(__name__)

    # Default paths
    input_path = "data/processed/organophosphates_filtered.csv"
    output_dir = "data/processed"
    
    # Check if input file exists
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run code/filter.py first to generate the filtered dataset.")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    generate_all_fingerprints(input_path, output_dir)

if __name__ == "__main__":
    main()
