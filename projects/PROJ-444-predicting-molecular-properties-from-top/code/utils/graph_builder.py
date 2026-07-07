import logging
from typing import List, Tuple, Optional, Dict, Any
import os
import logging.handlers
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
except ImportError:
    raise ImportError("rdkit is required for graph_builder. Install via pip install rdkit.")

# Configure logger for invalid SMILES
# We will initialize this lazily in log_invalid_smiles to avoid file handle issues during import
_invalid_smiles_logger = None

def _get_invalid_smiles_logger():
    global _invalid_smiles_logger
    if _invalid_smiles_logger is None:
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "invalid_smiles.log"
        
        _invalid_smiles_logger = logging.getLogger("invalid_smiles")
        _invalid_smiles_logger.setLevel(logging.WARNING)
        
        # Remove existing handlers to prevent duplicates if called multiple times
        _invalid_smiles_logger.handlers.clear()
        
        handler = logging.FileHandler(log_file, mode='a')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        _invalid_smiles_logger.addHandler(handler)
        
        # Prevent propagation to root logger to avoid double logging if root is configured
        _invalid_smiles_logger.propagate = False
        
    return _invalid_smiles_logger

def log_invalid_smiles(smiles: str, reason: str):
    """
    Logs invalid SMILES strings to data/logs/invalid_smiles.log.
    
    Args:
        smiles: The invalid SMILES string.
        reason: The reason for invalidity.
    """
    logger = _get_invalid_smiles_logger()
    logger.warning(f"Invalid SMILES: '{smiles}' - Reason: {reason}")

def is_valid_molecule(smiles: str) -> bool:
    """
    Checks if a SMILES string represents a valid molecule.
    
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

def build_molecular_graph(smiles: str) -> Optional[Any]:
    """
    Builds an RDKit molecular graph from a SMILES string.
    
    Args:
        smiles: SMILES string.
        
    Returns:
        RDKit Mol object if successful, None otherwise.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            log_invalid_smiles(smiles, "RDKit failed to parse SMILES")
            return None
        # Sanitize to ensure graph validity (optional but recommended)
        Chem.SanitizeMol(mol)
        return mol
    except Exception as e:
        log_invalid_smiles(smiles, f"Exception during graph build: {str(e)}")
        return None

def get_molecular_weight(mol: Any) -> float:
    """
    Calculates the molecular weight of an RDKit Mol object.
    
    Args:
        mol: RDKit Mol object.
        
    Returns:
        Molecular weight as float.
    """
    if mol is None:
        return 0.0
    return Descriptors.MolWt(mol)

def build_graphs_from_smiles_list(smiles_list: List[str]) -> Tuple[List[Any], List[str]]:
    """
    Builds molecular graphs from a list of SMILES strings.
    Logs invalid ones and skips them.
    
    Args:
        smiles_list: List of SMILES strings.
        
    Returns:
        Tuple of (valid_mol_list, skipped_smiles_list)
    """
    valid_mols = []
    skipped = []
    
    for smiles in smiles_list:
        mol = build_molecular_graph(smiles)
        if mol is not None:
            valid_mols.append(mol)
        else:
            skipped.append(smiles)
            
    return valid_mols, skipped

def validate_graph_structure(mol: Any) -> bool:
    """
    Validates that the molecular graph has the expected structure (e.g., not empty).
    
    Args:
        mol: RDKit Mol object.
        
    Returns:
        True if valid structure, False otherwise.
    """
    if mol is None:
        return False
    # Check for at least one atom
    if mol.GetNumAtoms() == 0:
        return False
    return True

def main():
    """
    Main entry point for testing graph builder utilities.
    """
    test_smiles = [
        "CCO",  # Ethanol - valid
        "invalid_smiles", # Invalid
        "c1ccccc1", # Benzene - valid
        "", # Empty
        None # None type
    ]
    
    for s in test_smiles:
        if s is None:
            print(f"Testing None: Invalid (expected)")
            continue
        mol = build_molecular_graph(s)
        if mol:
            print(f"SMILES: {s} -> Valid. MW: {get_molecular_weight(mol):.2f}")
        else:
            print(f"SMILES: {s} -> Invalid (logged)")

if __name__ == "__main__":
    main()
