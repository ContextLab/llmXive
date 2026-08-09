"""
SMILES Validation Utility.

This module provides functions to validate SMILES strings using RDKit.
It is used by the ingestion pipeline (T048) and preprocessing (T014)
to ensure data integrity before processing.

The primary entry point is `validate_smiles(smiles_list)`, which returns
a list of invalid SMILES strings. This allows downstream tasks to filter
or log excluded molecules without raising exceptions for bad input.
"""

import logging
from typing import List, Optional

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

logger = logging.getLogger(__name__)


def validate_smiles(smiles_list: List[str], strict: bool = True) -> List[str]:
    """
    Validate a list of SMILES strings.

    This function checks if each SMILES string is syntactically correct
    and can be parsed into a valid RDKit molecule object. It also performs
    basic sanity checks (e.g., non-empty, valid valence) if strict mode is on.

    Args:
        smiles_list: A list of SMILES strings to validate.
        strict: If True, performs additional checks like valence correctness
                and non-zero atom count. If False, only checks parseability.

    Returns:
        A list of SMILES strings that failed validation (invalid strings).
        If all are valid, returns an empty list.

    Raises:
        TypeError: If input is not a list of strings.
    """
    if not isinstance(smiles_list, list):
        raise TypeError("Input must be a list of SMILES strings.")

    invalid_smiles = []

    for idx, smiles in enumerate(smiles_list):
        if not isinstance(smiles, str):
            logger.warning(f"Item at index {idx} is not a string: {type(smiles)}")
            invalid_smiles.append(str(smiles))
            continue

        # Check for empty string
        if not smiles.strip():
            invalid_smiles.append(smiles)
            continue

        try:
            mol = Chem.MolFromSmiles(smiles)

            if mol is None:
                invalid_smiles.append(smiles)
                continue

            if strict:
                # Check for valid atom count (non-zero)
                if mol.GetNumAtoms() == 0:
                    invalid_smiles.append(smiles)
                    continue

                # Check for valid valence (SanitizeMol raises an exception if invalid)
                # We use a try/except block to catch sanitization errors
                try:
                    Chem.SanitizeMol(mol)
                except Exception:
                    invalid_smiles.append(smiles)
                    continue

        except Exception as e:
            # Catch any unexpected RDKit errors
            logger.debug(f"Error validating SMILES '{smiles[:50]}...': {e}")
            invalid_smiles.append(smiles)

    if invalid_smiles:
        logger.warning(f"Found {len(invalid_smiles)} invalid SMILES strings.")
    else:
        logger.info("All SMILES strings are valid.")

    return invalid_smiles


def is_valid_smiles(smiles: str, strict: bool = True) -> bool:
    """
    Check if a single SMILES string is valid.

    Args:
        smiles: The SMILES string to check.
        strict: If True, performs additional checks.

    Returns:
        True if valid, False otherwise.
    """
    return smiles not in validate_smiles([smiles], strict=strict)


def count_atoms(smiles: str) -> int:
    """
    Count the number of atoms in a molecule from its SMILES string.

    Args:
        smiles: The SMILES string.

    Returns:
        The number of atoms, or 0 if the SMILES is invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0
    return mol.GetNumAtoms()


def get_atom_types(smiles: str) -> Optional[List[str]]:
    """
    Get a list of atom types (symbols) for a molecule.

    Args:
        smiles: The SMILES string.

    Returns:
        A list of atom symbols (e.g., ['C', 'H', 'O']) or None if invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return [atom.GetSymbol() for atom in mol.GetAtoms()]


def get_hybridization(smiles: str) -> Optional[List[str]]:
    """
    Get a list of hybridization states for atoms in a molecule.

    Args:
        smiles: The SMILES string.

    Returns:
        A list of hybridization strings (e.g., ['SP3', 'SP2']) or None if invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return [atom.GetHybridization().name for atom in mol.GetAtoms()]


def get_charge(smiles: str) -> Optional[List[int]]:
    """
    Get a list of formal charges for atoms in a molecule.

    Args:
        smiles: The SMILES string.

    Returns:
        A list of formal charges or None if invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return [atom.GetFormalCharge() for atom in mol.GetAtoms()]


def main():
    """
    Simple CLI test for the validator.
    """
    import sys

    # Example test cases
    test_data = [
        "CCO",  # Valid: Ethanol
        "c1ccccc1",  # Valid: Benzene
        "CC(=O)O",  # Valid: Acetic Acid
        "invalid_smiles",  # Invalid
        "",  # Invalid: Empty
        "C[C@H](O)C",  # Valid: Stereochemistry
        "C1CCCCC1C1CCCCC1", # Valid: Decalin
        "C[C@@H](O)C", # Valid: Stereochemistry
        "C[Na]", # Invalid valence (usually)
        "C1=CC=CC=C1", # Valid: Benzene (alternative)
    ]

    print("Running SMILES Validation Test...")
    print("-" * 50)

    invalids = validate_smiles(test_data, strict=True)

    print(f"Total tested: {len(test_data)}")
    print(f"Invalid found: {len(invalids)}")
    print("Invalid SMILES:")
    for s in invalids:
        print(f"  - {s}")

    print("-" * 50)
    print("Validation complete.")

    if len(invalids) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    # Setup basic logging for CLI usage
    logging.basicConfig(level=logging.INFO)
    main()