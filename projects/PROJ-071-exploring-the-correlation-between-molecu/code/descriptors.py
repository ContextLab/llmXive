import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.Descriptors import wiener_index, balabanj
from logging_config import get_logger, DescriptorCalculationError
from pathlib import Path
import logging

logger = get_logger(__name__)

class AtomValenceException(Exception):
    """Custom exception for non-standard valence errors."""
    pass

def log_error_to_file(smiles: str, error_msg: str, log_path: str):
    """
    Logs the error to a file.
    """
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(f"{smiles}: {error_msg}\n")
    logger.warning(f"Logged error for {smiles} to {log_path}")

def calculate_tpsa(mol: Chem.Mol) -> float:
    """Calculate Topological Polar Surface Area."""
    return rdMolDescriptors.CalcTPSA(mol)

def calculate_rotatable_bonds(mol: Chem.Mol) -> int:
    """Calculate Rotatable Bond Count."""
    return rdMolDescriptors.CalcNumRotatableBonds(mol)

def calculate_mw(mol: Chem.Mol) -> float:
    """Calculate Molecular Weight."""
    return Descriptors.MolWt(mol)

def calculate_aromatic_rings(mol: Chem.Mol) -> int:
    """Calculate Aromatic Ring Count."""
    return rdMolDescriptors.CalcNumAromaticRings(mol)

def calculate_wiener_index(mol: Chem.Mol) -> float:
    """Calculate Wiener Index."""
    try:
        return wiener_index(mol)
    except Exception as e:
        raise AtomValenceException(f"Wiener index calculation failed: {e}")

def calculate_zagreb_index(mol: Chem.Mol) -> float:
    """Calculate Zagreb Index."""
    try:
        # RDKit does not have a direct 'Zagreb Index' in Descriptors, 
        # but we can compute the First Zagreb Index (sum of squared degrees).
        # Using the adjacency matrix approach or a specific descriptor if available.
        # For simplicity and robustness, we use a known approximation or the 'MolLogP' if that was intended,
        # but strictly following the prompt, we attempt to calculate it.
        # RDKit's `rdMolDescriptors` has `CalcNumZagreb`? No.
        # We will implement a simple version using the molecular graph.
        adj = rdMolDescriptors.GetAdjacencyMatrix(mol)
        degrees = np.sum(adj, axis=1)
        zagreb = np.sum(degrees ** 2)
        return float(zagreb)
    except Exception as e:
        raise AtomValenceException(f"Zagreb index calculation failed: {e}")

def calculate_descriptors_for_molecule(smiles: str) -> Dict[str, float]:
    """
    Calculates all descriptors for a single molecule.
    Flags/excludes molecules with non-standard valence.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise AtomValenceException("Invalid SMILES string or non-standard valence detected during parsing.")
    
    # Check for valence errors explicitly
    # RDKit usually sanitizes, but we can check for specific issues
    try:
        Chem.SanitizeMol(mol)
    except Exception as e:
        raise AtomValenceException(f"Sanitization failed (valence issue): {e}")

    try:
        return {
            'tpsa': calculate_tpsa(mol),
            'rotatable_bonds': calculate_rotatable_bonds(mol),
            'mw': calculate_mw(mol),
            'aromatic_rings': calculate_aromatic_rings(mol),
            'wiener_index': calculate_wiener_index(mol),
            'zagreb_index': calculate_zagreb_index(mol)
        }
    except AtomValenceException as e:
        raise e
    except Exception as e:
        raise DescriptorCalculationError(f"Unexpected error calculating descriptors: {e}")

def calculate_descriptors_batch(df: pd.DataFrame, smiles_col: str = 'smiles', log_path: str = 'data/errors.log') -> pd.DataFrame:
    """
    Calculates descriptors for a batch of molecules.
    Logs errors to `log_path` and excludes invalid molecules.
    """
    results = []
    valid_rows = []
    
    logger.info(f"Starting descriptor calculation for {len(df)} molecules...")
    
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        try:
            desc = calculate_descriptors_for_molecule(smiles)
            desc['smiles'] = smiles
            results.append(desc)
            valid_rows.append(idx)
        except AtomValenceException as e:
            log_error_to_file(smiles, str(e), log_path)
            logger.debug(f"Skipped molecule at index {idx} due to valence error: {smiles}")
        except Exception as e:
            log_error_to_file(smiles, f"General error: {e}", log_path)
            logger.debug(f"Skipped molecule at index {idx} due to error: {smiles}")
    
    if not results:
        logger.warning("No valid molecules found for descriptor calculation.")
        return pd.DataFrame()
    
    desc_df = pd.DataFrame(results)
    logger.info(f"Successfully calculated descriptors for {len(desc_df)} molecules. {len(df) - len(desc_df)} excluded.")
    return desc_df

def main():
    """
    Main entry point for descriptor calculation.
    Reads from merged dataset and writes to processed descriptors file.
    """
    from config import get_config
    import os

    config = get_config()
    input_path = config.get('paths', {}).get('merged_dataset', 'data/processed/merged_drugs.csv')
    output_path = config.get('paths', {}).get('descriptors_output', 'data/processed/descriptors.csv')
    log_path = 'data/errors.log'

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return 1

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    logger.info(f"Calculating descriptors...")
    desc_df = calculate_descriptors_batch(df, smiles_col='smiles', log_path=log_path)

    if desc_df.empty:
        logger.error("No descriptors calculated. Check errors.log.")
        return 1

    # Merge back if needed, or just save descriptors
    # The task says "Save merged dataset" in T017, but T014 is just calculation.
    # We save the descriptors here.
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    desc_df.to_csv(output_path, index=False)
    logger.info(f"Descriptors saved to {output_path}")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())