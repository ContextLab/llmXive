"""
Utilities for data ingestion: unit conversion, weight-fraction validation, and SMILES parsing.
"""
from typing import Union, List, Tuple, Optional
from rdkit import Chem
from rdkit.Chem import Descriptors
import logging

logger = logging.getLogger(__name__)

def celsius_to_kelvin(celsius: float) -> float:
    """Convert temperature from Celsius to Kelvin."""
    return celsius + 273.15

def pascal_to_gpa(pa: float) -> float:
    """Convert pressure/stress from Pascal to GPa."""
    return pa / 1e9

def validate_weight_fractions(fractions: List[float], tolerance: float = 0.02) -> Tuple[bool, str]:
    """
    Validate that weight fractions sum to approximately 1.0 within a given tolerance.

    Args:
        fractions: List of weight fractions.
        tolerance: Allowed deviation from 1.0 (default ±0.02).

    Returns:
        Tuple of (is_valid, message).
    """
    if not fractions:
        return False, "Weight fractions list is empty."

    total = sum(fractions)
    if abs(total - 1.0) <= tolerance:
        return True, f"Weight fractions sum to {total:.4f}, which is valid within tolerance {tolerance}."
    elif total > 1.0 + tolerance:
        return False, f"Weight fractions sum to {total:.4f}, which exceeds 1.0 + tolerance ({1.0 + tolerance})."
    else:
        return False, f"Weight fractions sum to {total:.4f}, which is below 1.0 - tolerance ({1.0 - tolerance})."

def is_valid_smiles(smiles: str) -> bool:
    """
    Validate a SMILES string using RDKit.

    Args:
        smiles: SMILES string to validate.

    Returns:
        True if the SMILES is valid and can be parsed into a molecule, False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        # Additional check: ensure the molecule has at least one atom
        if mol.GetNumAtoms() == 0:
            return False
        return True
    except Exception as e:
        logger.warning(f"RDKit failed to parse SMILES '{smiles}': {e}")
        return False

def parse_smiles_to_mol(smiles: str):
    """
    Parse a SMILES string into an RDKit Mol object.

    Args:
        smiles: SMILES string.

    Returns:
        RDKit Mol object if valid, None otherwise.
    """
    if not is_valid_smiles(smiles):
        return None
    return Chem.MolFromSmiles(smiles)
