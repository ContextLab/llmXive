import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.Descriptors import wiener_index, balabanj
import logging
from pathlib import Path
from datetime import datetime

# Import existing logging utilities
from logging_config import get_logger, DescriptorCalculationError

logger = get_logger(__name__)

# Constants for error logging
ERROR_LOG_PATH = Path("data/errors.log")

def calculate_tpsa(mol: Chem.Mol) -> float:
    """Calculate Topological Polar Surface Area."""
    if mol is None:
        return np.nan
    return rdMolDescriptors.CalcTPSA(mol)

def calculate_rotatable_bonds(mol: Chem.Mol) -> int:
    """Calculate number of rotatable bonds."""
    if mol is None:
        return np.nan
    return rdMolDescriptors.CalcNumRotatableBonds(mol)

def calculate_mw(mol: Chem.Mol) -> float:
    """Calculate Molecular Weight."""
    if mol is None:
        return np.nan
    return Descriptors.MolWt(mol)

def calculate_aromatic_rings(mol: Chem.Mol) -> int:
    """Calculate number of aromatic rings."""
    if mol is None:
        return np.nan
    return rdMolDescriptors.CalcNumAromaticRings(mol)

def calculate_wiener_index(mol: Chem.Mol) -> float:
    """Calculate Wiener Index."""
    if mol is None:
        return np.nan
    try:
        return wiener_index(mol)
    except Exception:
        logger.warning("Wiener index calculation failed for molecule")
        return np.nan

def calculate_zagreb_index(mol: Chem.Mol) -> float:
    """Calculate Zagreb Index."""
    if mol is None:
        return np.nan
    try:
        return rdMolDescriptors.CalcZagrebIndex(mol)
    except Exception:
        logger.warning("Zagreb index calculation failed for molecule")
        return np.nan

def _log_error(smiles: str, error_type: str, details: str):
    """Log molecule errors to data/errors.log."""
    ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {error_type}: {details} | SMILES: {smiles}\n"
    
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    logger.error(f"Logged error for {smiles[:50]}...: {error_type}")

def _is_valid_molecule(mol: Chem.Mol, smiles: str) -> bool:
    """
    Check if a molecule is valid for descriptor calculation.
    Flags/excludes molecules with non-standard valence or parsing errors.
    """
    if mol is None:
        _log_error(smiles, "PARSE_ERROR", "RDKit failed to parse SMILES")
        return False

    # Check for sanitization issues (valence errors, etc.)
    # If sanitize=False was used during parsing, we must try to sanitize here
    # to catch valence errors explicitly.
    try:
        Chem.SanitizeMol(mol)
    except Chem.rdchem.KekulizeException as e:
        _log_error(smiles, "KEKULIZE_ERROR", str(e))
        return False
    except Chem.rdchem.AtomValenceException as e:
        _log_error(smiles, "VALENCE_ERROR", str(e))
        return False
    except Exception as e:
        _log_error(smiles, "SANITIZATION_ERROR", str(e))
        return False

    return True

def calculate_descriptors_for_molecule(smiles: str) -> Optional[Dict[str, float]]:
    """
    Calculate all descriptors for a single molecule.
    Returns None if the molecule is invalid (logs error).
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        
        if not _is_valid_molecule(mol, smiles):
            return None

        return {
            "TPSA": calculate_tpsa(mol),
            "RotatableBonds": calculate_rotatable_bonds(mol),
            "MW": calculate_mw(mol),
            "AromaticRings": calculate_aromatic_rings(mol),
            "WienerIndex": calculate_wiener_index(mol),
            "ZagrebIndex": calculate_zagreb_index(mol)
        }
    except Exception as e:
        _log_error(smiles, "UNEXPECTED_ERROR", str(e))
        return None

def calculate_descriptors_batch(df: pd.DataFrame, smiles_col: str = "SMILES") -> pd.DataFrame:
    """
    Calculate descriptors for a batch of molecules in a DataFrame.
    Invalid molecules are excluded from the result and logged.
    """
    logger.info(f"Starting descriptor calculation for {len(df)} molecules")
    
    results = []
    valid_count = 0
    
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        if pd.isna(smiles) or not isinstance(smiles, str):
            _log_error(str(smiles), "INVALID_INPUT", "Non-string or NaN SMILES")
            continue
            
        descriptors = calculate_descriptors_for_molecule(smiles)
        
        if descriptors is not None:
            result_row = row.to_dict()
            result_row.update(descriptors)
            results.append(result_row)
            valid_count += 1
        else:
            # Molecule was invalid and logged in calculate_descriptors_for_molecule
            continue
    
    logger.info(f"Descriptor calculation complete. Valid: {valid_count}, Excluded: {len(df) - valid_count}")
    
    if not results:
        return pd.DataFrame()
        
    return pd.DataFrame(results)

def main():
    """
    Main entry point for running descriptor calculation on a dataset.
    Expects a CSV file at data/processed/merged_drugs.csv (or similar).
    """
    # Example usage logic if run directly
    input_path = Path("data/processed/merged_drugs.csv")
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    if "SMILES" not in df.columns:
        logger.error("Input CSV must contain a 'SMILES' column")
        return

    processed_df = calculate_descriptors_batch(df)
    
    output_path = Path("data/processed/descriptors_added.csv")
    processed_df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

if __name__ == "__main__":
    main()
