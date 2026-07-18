import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.Descriptors import wiener_index, balabanj
from pathlib import Path
import logging

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def get_data_path():
    config = get_config()
    return Path(config.get("data_dir", "data"))

class AtomValenceException(Exception):
    """Exception raised for invalid valence in molecules."""
    pass

def log_error_to_file(error_msg: str, log_file: Optional[Path] = None):
    """
    Log an error message to a file.
    """
    if log_file is None:
        log_file = get_data_path() / "errors.log"
    
    with open(log_file, 'a') as f:
        f.write(f"{pd.Timestamp.now()}: {error_msg}\n")

def validate_molecule(smiles: str) -> Tuple[Optional[Chem.Mol], Optional[str]]:
    """
    Validate a SMILES string and return the RDKit molecule object.
    Returns (mol, error_message).
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, f"Failed to parse SMILES: {smiles}"
        
        # Check for valence issues
        Chem.SanitizeMol(mol)
        return mol, None
    except Exception as e:
        return None, str(e)

def calculate_tpsa(mol: Chem.Mol) -> float:
    """
    Calculate Topological Polar Surface Area (TPSA).
    """
    return rdMolDescriptors.CalcTPSA(mol)

def calculate_rotatable_bonds(mol: Chem.Mol) -> int:
    """
    Calculate the number of rotatable bonds.
    """
    return rdMolDescriptors.CalcNumRotatableBonds(mol)

def calculate_mw(mol: Chem.Mol) -> float:
    """
    Calculate Molecular Weight.
    """
    return Descriptors.MolWt(mol)

def calculate_aromatic_rings(mol: Chem.Mol) -> int:
    """
    Calculate the number of aromatic rings.
    """
    return rdMolDescriptors.CalcNumAromaticRings(mol)

def calculate_wiener_index(mol: Chem.Mol) -> float:
    """
    Calculate the Wiener Index.
    """
    return wiener_index(mol)

def calculate_zagreb_index(mol: Chem.Mol) -> float:
    """
    Calculate the Zagreb Index.
    """
    # Using the Balaban J index as a proxy if Zagreb is not directly available
    # Note: RDKit does not have a direct Zagreb index function, so we use Balaban J
    # If a specific Zagreb index is required, it might need custom implementation
    return balabanj(mol)

def calculate_descriptors_for_molecule(smiles: str) -> Dict[str, Any]:
    """
    Calculate all descriptors for a single molecule.
    """
    mol, error = validate_molecule(smiles)
    if error:
        log_error_to_file(error)
        return {'smiles': smiles, 'error': error}
    
    descriptors = {
        'smiles': smiles,
        'tpsa': calculate_tpsa(mol),
        'rotatable_bonds': calculate_rotatable_bonds(mol),
        'mw': calculate_mw(mol),
        'aromatic_rings': calculate_aromatic_rings(mol),
        'wiener_index': calculate_wiener_index(mol),
        'zagreb_index': calculate_zagreb_index(mol)
    }
    return descriptors

def calculate_descriptors_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate descriptors for a batch of molecules.
    """
    results = []
    for idx, row in df.iterrows():
        if pd.isna(row['smiles']):
            continue
        descriptors = calculate_descriptors_for_molecule(row['smiles'])
        results.append(descriptors)
    
    return pd.DataFrame(results)

def main():
    config = get_config()
    logger.info("Starting descriptor calculation")
    
    # Load data
    input_path = get_data_path() / "processed" / "merged_drugs.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    df = pd.read_csv(input_path)
    
    # Calculate descriptors
    descriptors_df = calculate_descriptors_batch(df)
    
    # Save results
    output_path = get_data_path() / "processed" / "descriptors.csv"
    descriptors_df.to_csv(output_path, index=False)
    logger.info(f"Saved descriptors to {output_path}")

if __name__ == "__main__":
    main()
