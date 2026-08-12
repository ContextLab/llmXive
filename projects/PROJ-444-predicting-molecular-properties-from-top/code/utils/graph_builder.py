import logging
from typing import List, Tuple, Optional, Dict, Any
import os
import logging.handlers
from pathlib import Path
import rdkit
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

# Configure logging to a specific file as per task requirement
def setup_invalid_smiles_logger(log_path: str) -> logging.Logger:
    """
    Sets up a dedicated logger for invalid SMILES that writes to a specific file.
    """
    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Ensure directory exists
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    return logger

# Global logger instance, initialized lazily or by main
_invalid_smiles_logger = None

def log_invalid_smiles(smiles: str, reason: str, log_path: str = "data/logs/invalid_smiles.log"):
    """
    Logs an invalid SMILES string and the reason for invalidity.
    Initializes the logger if not already done.
    """
    global _invalid_smiles_logger
    if _invalid_smiles_logger is None:
        _invalid_smiles_logger = setup_invalid_smiles_logger(log_path)
    
    _invalid_smiles_logger.info(f"SMILES: {smiles} | Reason: {reason}")

def is_valid_molecule(smiles: str) -> bool:
    """
    Checks if a SMILES string represents a valid molecule using RDKit.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def build_molecular_graph(smiles: str) -> Optional[Chem.Mol]:
    """
    Builds an RDKit molecule object from a SMILES string.
    Returns None if invalid.
    """
    if not is_valid_molecule(smiles):
        return None
    return Chem.MolFromSmiles(smiles)

def get_molecular_weight(mol: Chem.Mol) -> float:
    """
    Calculates the molecular weight of an RDKit molecule.
    """
    if mol is None:
        return 0.0
    return Descriptors.MolWt(mol)

def build_graphs_from_smiles_list(
    smiles_list: List[str], 
    log_path: str = "data/logs/invalid_smiles.log"
) -> Tuple[List[Chem.Mol], List[Tuple[str, str]]]:
    """
    Builds a list of valid molecular graphs from a list of SMILES strings.
    Logs invalid SMILES to the specified log file.
    Returns a tuple of (valid_molecules, invalid_records) where invalid_records
    is a list of (smiles, reason) tuples.
    """
    valid_molecules = []
    invalid_records = []
    
    # Initialize logger for this batch
    logger = setup_invalid_smiles_logger(log_path)
    
    for smiles in smiles_list:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is not None:
                valid_molecules.append(mol)
            else:
                # RDKit returns None for invalid SMILES, often with a warning
                # We log it as invalid
                logger.warning(f"SMILES: {smiles} | Reason: RDKit failed to parse")
                invalid_records.append((smiles, "RDKit parse failure"))
        except Exception as e:
            logger.warning(f"SMILES: {smiles} | Reason: Exception - {str(e)}")
            invalid_records.append((smiles, f"Exception: {str(e)}"))
    
    return valid_molecules, invalid_records

def validate_graph_structure(mol: Chem.Mol) -> bool:
    """
    Validates the internal structure of an RDKit molecule.
    Checks for basic connectivity and atom validity.
    """
    if mol is None:
        return False
    try:
        # Check if molecule has atoms
        if mol.GetNumAtoms() == 0:
            return False
        # Check if molecule has bonds (optional, but good for graph connectivity)
        # Some molecules might be single atoms, but usually we expect bonds for TDA
        # For this task, we just ensure it's a valid RDKit object
        Chem.SanitizeMol(mol)
        return True
    except Exception:
        return False

def main():
    """
    Main function for testing the graph builder module.
    """
    test_smiles = [
        "CCO",       # Valid: Ethanol
        "invalid",   # Invalid
        "c1ccccc1",  # Valid: Benzene
        "",          # Invalid
        "C(C)(C)C",  # Valid: Isobutane
    ]
    
    print("Testing graph builder...")
    valid_mols, invalids = build_graphs_from_smiles_list(test_smiles, log_path="data/logs/invalid_smiles.log")
    
    print(f"Valid molecules found: {len(valid_mols)}")
    print(f"Invalid molecules logged: {len(invalids)}")
    
    for mol in valid_mols:
        print(f"MW: {get_molecular_weight(mol):.2f}, Atoms: {mol.GetNumAtoms()}")
    
    if invalids:
        print("\nInvalid SMILES details:")
        for smiles, reason in invalids:
            print(f"  {smiles}: {reason}")

if __name__ == "__main__":
    main()
