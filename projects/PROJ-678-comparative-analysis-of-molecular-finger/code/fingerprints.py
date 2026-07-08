import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import DataStructs
import logging
from typing import List, Optional, Tuple
import os
import sys

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from utils import get_logger, init_random_seed
from constants import MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS, TANIMOTO_THRESHOLD

logger = get_logger(__name__)

def generate_morgan_fingerprint(mol: Chem.Mol, radius: int = MORGAN_RADIUS, n_bits: int = MORGAN_BITS) -> np.ndarray:
    """
    Generate a Morgan fingerprint (ECFP) for a given molecule.
    
    Args:
        mol: RDKit Mol object
        radius: Radius of the fingerprint (default 2)
        n_bits: Number of bits in the fingerprint (default 2048)
        
    Returns:
        Numpy array of fingerprint bits
    """
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.int8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def generate_maccs_fingerprint(mol: Chem.Mol, n_bits: int = MACCS_BITS) -> np.ndarray:
    """
    Generate a MACCS key fingerprint for a given molecule.
    
    Args:
        mol: RDKit Mol object
        n_bits: Number of bits in the fingerprint (default 166)
        
    Returns:
        Numpy array of fingerprint bits
    """
    fp = MACCSkeys.GenMACCSKeys(mol)
    arr = np.zeros((n_bits,), dtype=np.int8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def calculate_tanimoto_similarity(fp1: np.ndarray, fp2: np.ndarray) -> float:
    """
    Calculate Tanimoto similarity between two fingerprint arrays.
    
    Args:
        fp1: First fingerprint array
        fp2: Second fingerprint array
        
    Returns:
        Tanimoto similarity coefficient (0.0 to 1.0)
    """
    # Convert numpy arrays back to RDKit ExplicitBitVect for accurate calculation
    # or calculate directly using numpy intersection/union logic
    intersection = np.sum(np.logical_and(fp1 > 0, fp2 > 0))
    union = np.sum(np.logical_or(fp1 > 0, fp2 > 0))
    
    if union == 0:
        return 0.0
    return intersection / union

def get_fingerprint_bit_info(mol: Chem.Mol, radius: int = MORGAN_RADIUS) -> dict:
    """
    Get information about which bits are set in the Morgan fingerprint and their origin.
    
    Args:
        mol: RDKit Mol object
        radius: Radius used for fingerprint generation
        
    Returns:
        Dictionary mapping bit indices to list of atom indices that contributed
    """
    fp = AllChem.GetMorganFingerprint(mol, radius)
    bit_info = {}
    fp.ToBitInfo(bit_info)
    return bit_info

def generate_fingerprints_batch(
    mols: List[Chem.Mol],
    batch_size: int = 500,
    memory_threshold_gb: float = 7.0
) -> Tuple[np.ndarray, np.ndarray, List[int]]:
    """
    Generate Morgan and MACCS fingerprints for a list of molecules in batches.
    
    Implements chunked processing if memory usage is estimated to exceed threshold.
    
    Args:
        mols: List of RDKit Mol objects
        batch_size: Number of molecules to process in one batch
        memory_threshold_gb: Memory threshold in GB to trigger chunking
        
    Returns:
        Tuple of (morgan_fingerprints, maccs_fingerprints, valid_indices)
        morgan_fingerprints: 2D numpy array (n_samples, MORGAN_BITS)
        maccs_fingerprints: 2D numpy array (n_samples, MACCS_BITS)
        valid_indices: List of indices of successfully processed molecules
    """
    # Estimate memory usage: 2048 bits + 166 bits per molecule * 4 bytes (float32)
    # Rough estimate per molecule: (2048 + 166) * 4 bytes ≈ 9KB
    estimated_memory_per_mol_mb = (MORGAN_BITS + MACCS_BITS) * 4 / (1024 * 1024)
    total_estimated_memory_gb = len(mols) * estimated_memory_per_mol_mb / 1024
    
    logger.info(f"Processing {len(mols)} molecules. Estimated memory: {total_estimated_memory_gb:.2f} GB")
    
    use_chunking = total_estimated_memory_gb > memory_threshold_gb
    
    if use_chunking:
        logger.info(f"Memory threshold ({memory_threshold_gb} GB) exceeded. Using chunked processing with batch_size={batch_size}")
    else:
        logger.info("Memory threshold not exceeded. Processing all molecules at once.")
    
    all_morgan_fps = []
    all_maccs_fps = []
    valid_indices = []
    
    start_idx = 0
    end_idx = len(mols) if not use_chunking else batch_size
    
    while start_idx < len(mols):
        batch_mols = mols[start_idx:end_idx]
        batch_morgan = []
        batch_maccs = []
        batch_valid_indices = []
        
        for i, mol in enumerate(batch_mols):
            if mol is None:
                logger.warning(f"Molecule at global index {start_idx + i} is None, skipping")
                continue
            
            try:
                morgan_fp = generate_morgan_fingerprint(mol)
                maccs_fp = generate_maccs_fingerprint(mol)
                batch_morgan.append(morgan_fp)
                batch_maccs.append(maccs_fp)
                batch_valid_indices.append(start_idx + i)
            except Exception as e:
                logger.error(f"Error processing molecule at index {start_idx + i}: {e}")
                continue
        
        if batch_morgan:
            all_morgan_fps.extend(batch_morgan)
            all_maccs_fps.extend(batch_maccs)
            valid_indices.extend(batch_valid_indices)
        
        logger.info(f"Processed batch {start_idx}-{end_idx}, total valid so far: {len(valid_indices)}")
        
        start_idx = end_idx
        if use_chunking:
            end_idx = min(start_idx + batch_size, len(mols))
        else:
            break  # Done if not chunking
    
    if not all_morgan_fps:
        logger.error("No valid fingerprints generated. Check input molecules.")
        return np.empty((0, MORGAN_BITS)), np.empty((0, MACCS_BITS)), []
    
    morgan_array = np.array(all_morgan_fps, dtype=np.int8)
    maccs_array = np.array(all_maccs_fps, dtype=np.int8)
    
    logger.info(f"Final fingerprint arrays: Morgan {morgan_array.shape}, MACCS {maccs_array.shape}")
    return morgan_array, maccs_array, valid_indices

def main():
    """
    Main entry point to generate fingerprints from the filtered dataset.
    Reads from data/processed/organophosphates_filtered.csv and saves to data/processed/fingerprints.npz
    """
    import pandas as pd
    from pathlib import Path
    
    init_random_seed(42)
    setup_logging()
    
    # Determine paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "processed" / "organophosphates_filtered.csv"
    output_path = project_root / "data" / "processed" / "fingerprints.npz"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T012 (filter.py) first to generate the filtered dataset.")
        sys.exit(1)
    
    logger.info(f"Loading compounds from {input_path}")
    df = pd.read_csv(input_path)
    
    # Load SMILES and convert to RDKit molecules
    smiles_list = df['smiles'].tolist()
    mols = [Chem.MolFromSmiles(s) for s in smiles_list]
    
    logger.info(f"Loaded {len(mols)} molecules. Converting to fingerprints...")
    
    morgan_fps, maccs_fps, valid_indices = generate_fingerprints_batch(mols)
    
    if len(valid_indices) == 0:
        logger.error("No valid fingerprints generated. Exiting.")
        sys.exit(1)
    
    # Save results
    # Filter original dataframe to keep only valid rows
    valid_df = df.iloc[valid_indices].reset_index(drop=True)
    
    # Save fingerprints and metadata
    np.savez(
        output_path,
        morgan_fingerprints=morgan_fps,
        maccs_fingerprints=maccs_fps,
        valid_indices=valid_indices,
        smiles=valid_df['smiles'].values,
        # Save other relevant columns if needed for downstream tasks
        # e.g., toxicity labels if present in the CSV
    )
    
    logger.info(f"Successfully saved fingerprints to {output_path}")
    logger.info(f"Total valid compounds: {len(valid_indices)}")
    logger.info(f"Morgan fingerprint shape: {morgan_fps.shape}")
    logger.info(f"MACCS fingerprint shape: {maccs_fps.shape}")
    
    # Optional: Log sample Tanimoto similarities for validation
    if len(valid_indices) > 1:
        sample_fp1 = morgan_fps[0]
        sample_fp2 = morgan_fps[1]
        sim = calculate_tanimoto_similarity(sample_fp1, sample_fp2)
        logger.info(f"Sample Tanimoto similarity (first two valid): {sim:.4f}")

if __name__ == "__main__":
    main()