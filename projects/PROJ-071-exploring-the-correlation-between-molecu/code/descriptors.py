import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.Descriptors import wiener_index, balabanj
import logging
from pathlib import Path
from config import get_config
from logging_config import get_logger

# Use config for paths
def get_data_path(relative_path: str) -> Path:
    config = get_config()
    return Path(config.get("data_dir", "data")) / relative_path

class AtomValenceException(Exception):
    """Custom exception for valence errors."""
    pass

def log_error_to_file(smiles: str, error_msg: str, log_path: Optional[Path] = None):
    """
    Logs errors to a file.
    """
    if log_path is None:
        log_path = get_data_path("errors.log")
    with open(log_path, 'a') as f:
        f.write(f"{smiles}: {error_msg}\n")

def validate_molecule(smiles: str) -> Optional[Chem.Mol]:
    """
    Validates a SMILES string and returns the RDKit molecule object.
    Raises AtomValenceException if valence errors are detected.
    """
    logger = get_logger(__name__)
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise AtomValenceException(f"Invalid SMILES: {smiles}")
        
        # Check for valence errors
        Chem.SanitizeMol(mol)
        return mol
    except Exception as e:
        logger.warning(f"Validation failed for {smiles}: {str(e)}")
        log_error_to_file(smiles, str(e))
        raise AtomValenceException(f"Valence error for {smiles}: {str(e)}")

def calculate_tpsa(mol: Chem.Mol) -> float:
    """Calculate Topological Polar Surface Area."""
    return Descriptors.TPSA(mol)

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
        # Fallback or custom implementation if needed
        return 0.0

def calculate_zagreb_index(mol: Chem.Mol) -> float:
    """Calculate Zagreb Index."""
    try:
        # RDKit does not have a direct Zagreb index function in Descriptors
        # Using a custom implementation or alternative
        # For now, returning a placeholder or using a similar descriptor
        # Zagreb index is sum of squared degrees of vertices
        # This is a simplified version
        mol = Chem.AddHs(mol)
        graph = Chem.GetAdjacencyMatrix(mol)
        degrees = np.sum(graph, axis=1)
        zagreb = np.sum(degrees ** 2)
        return float(zagreb)
    except Exception as e:
        return 0.0

def calculate_descriptors_for_molecule(smiles: str) -> Dict[str, float]:
    """
    Calculates all descriptors for a single molecule.
    """
    logger = get_logger(__name__)
    try:
        mol = validate_molecule(smiles)
        descriptors = {
            'tpsa': calculate_tpsa(mol),
            'rotatable_bonds': calculate_rotatable_bonds(mol),
            'mw': calculate_mw(mol),
            'aromatic_rings': calculate_aromatic_rings(mol),
            'wiener_index': calculate_wiener_index(mol),
            'zagreb_index': calculate_zagreb_index(mol)
        }
        return descriptors
    except AtomValenceException as e:
        logger.error(f"Skipping molecule due to valence error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calculating descriptors for {smiles}: {str(e)}")
        return None

def calculate_descriptors_batch(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """
    Calculates descriptors for a batch of molecules in a DataFrame.
    """
    logger = get_logger(__name__)
    results = []
    for idx, row in df.iterrows():
        descriptors = calculate_descriptors_for_molecule(row[smiles_col])
        if descriptors:
            results.append(descriptors)
        else:
            # Log error and skip
            log_error_to_file(row[smiles_col], "Descriptor calculation failed")
    
    descriptors_df = pd.DataFrame(results)
    return descriptors_df

def main():
    """
    Main entry point for descriptor calculation.
    """
    logger = get_logger(__name__)
    logger.info("Starting descriptor calculation...")
    
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    processed_dir = data_dir / "processed"
    input_path = processed_dir / "merged_drugs.csv"
    output_path = processed_dir / "descriptors.csv"
    
    if not input_path.exists():
        logger.error(f"Input file {input_path} not found.")
        return
    
    df = pd.read_csv(input_path)
    descriptors_df = calculate_descriptors_batch(df)
    
    # Merge with original data
    merged_df = pd.concat([df.reset_index(drop=True), descriptors_df.reset_index(drop=True)], axis=1)
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Descriptors saved to {output_path}")

if __name__ == "__main__":
    main()
