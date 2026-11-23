"""
SMILES Validation Utilities for llmXive Molecular Surface Area Prediction.

This module provides robust validation for SMILES strings using RDKit.
It is designed to be used by ingestion (T048) and preprocessing (T014) tasks
to filter out syntactically invalid molecular representations before processing.
"""

import logging
from typing import List, Optional, Tuple

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Configure local logger instance
logger = logging.getLogger(__name__)


def is_valid_smiles(smiles: str) -> bool:
    """
    Check if a single SMILES string is syntactically valid.

    Args:
        smiles: The SMILES string to validate.

    Returns:
        True if the SMILES is valid and can be parsed into an RDKit Mol object,
        False otherwise.
    """
    if not isinstance(smiles, str) or not smiles.strip():
        return False

    try:
        mol = Chem.MolFromSmiles(smiles)
        # MolFromSmiles returns None if parsing fails
        if mol is None:
            return False
        
        # Additional check: ensure the molecule has at least one atom
        # (Some parsers might create an empty mol for edge cases)
        if mol.GetNumAtoms() == 0:
            return False
        
        return True
    except Exception as e:
        logger.debug(f"SMILES validation exception for '{smiles[:20]}...': {e}")
        return False


def count_atoms(smiles: str) -> int:
    """
    Count the number of atoms in a SMILES string.

    Args:
        smiles: The SMILES string.

    Returns:
        The number of atoms, or 0 if the SMILES is invalid.
    """
    if not is_valid_smiles(smiles):
        return 0
    
    mol = Chem.MolFromSmiles(smiles)
    return mol.GetNumAtoms()


def get_atom_types(mol: Chem.Mol) -> List[int]:
    """
    Extract atom types (atomic numbers) from an RDKit Mol object.

    Args:
        mol: An RDKit Mol object.

    Returns:
        A list of atomic integers representing atom types.
    """
    if mol is None:
        return []
    return [atom.GetAtomicNum() for atom in mol.GetAtoms()]


def get_hybridization(mol: Chem.Mol) -> List[int]:
    """
    Extract hybridization states from an RDKit Mol object.

    Args:
        mol: An RDKit Mol object.

    Returns:
        A list of integers representing hybridization states
        (mapped from rdkit.Chem.rdchem.HybridizationType).
    """
    if mol is None:
        return []
    
    # Map HybridizationType enum to int for storage
    # 0: S, 1: SP, 2: SP2, 3: SP3, 4: SP3D, 5: SP3D2, 6: OTHER
    hybrid_map = {
        Chem.rdchem.HybridizationType.S: 0,
        Chem.rdchem.HybridizationType.SP: 1,
        Chem.rdchem.HybridizationType.SP2: 2,
        Chem.rdchem.HybridizationType.SP3: 3,
        Chem.rdchem.HybridizationType.SP3D: 4,
        Chem.rdchem.HybridizationType.SP3D2: 5,
        Chem.rdchem.HybridizationType.OTHER: 6,
    }
    
    return [hybrid_map.get(atom.GetHybridization(), 6) for atom in mol.GetAtoms()]


def get_charge(mol: Chem.Mol) -> List[int]:
    """
    Extract formal charges from an RDKit Mol object.

    Args:
        mol: An RDKit Mol object.

    Returns:
        A list of integers representing formal charges.
    """
    if mol is None:
        return []
    return [atom.GetFormalCharge() for atom in mol.GetAtoms()]


def validate_smiles(smiles_list: List[str]) -> List[str]:
    """
    Validate a list of SMILES strings and return a list of invalid ones.

    This function is the primary entry point for T048 and T014.
    It iterates through the provided list, checks syntax using RDKit,
    and collects any strings that fail validation.

    Args:
        smiles_list: A list of SMILES strings to validate.

    Returns:
        A list of SMILES strings that were found to be invalid.
        Returns an empty list if all inputs are valid.
    """
    invalid_smiles = []
    
    for i, smiles in enumerate(smiles_list):
        if not isinstance(smiles, str):
            invalid_smiles.append(str(smiles))
            continue
        
        if not is_valid_smiles(smiles):
            invalid_smiles.append(smiles)
    
    if invalid_smiles:
        logger.warning(f"Found {len(invalid_smiles)} invalid SMILES out of {len(smiles_list)} inputs.")
    
    return invalid_smiles


def main():
    """
    CLI entry point for testing the validator.
    Reads a list of SMILES from stdin (newline separated) or arguments,
    and prints the count of valid/invalid.
    """
    import sys
    
    if len(sys.argv) > 1:
        # Treat arguments as SMILES strings
        test_smiles = sys.argv[1:]
    else:
        # Read from stdin if no args
        test_smiles = [line.strip() for line in sys.stdin if line.strip()]

    if not test_smiles:
        print("No SMILES provided.")
        return

    invalid = validate_smiles(test_smiles)
    
    print(f"Total inputs: {len(test_smiles)}")
    print(f"Valid: {len(test_smiles) - len(invalid)}")
    print(f"Invalid: {len(invalid)}")
    
    if invalid:
        print("Invalid SMILES found:")
        for s in invalid:
            print(f"  - {s}")

if __name__ == "__main__":
    main()