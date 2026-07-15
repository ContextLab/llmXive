from typing import Union, List, Tuple, Optional
from rdkit import Chem
from rdkit.Chem import Descriptors
import logging

logger = logging.getLogger(__name__)

def celsius_to_kelvin(temp_c: Union[int, float]) -> float:
    """Converts temperature from Celsius to Kelvin."""
    return float(temp_c) + 273.15

def pascal_to_gpa(pressure_pa: Union[int, float]) -> float:
    """Converts pressure from Pascals to GigaPascals."""
    return float(pressure_pa) / 1e9

def validate_weight_fractions(
    fractions: List[float], 
    tolerance: float = 0.02
) -> bool:
    """
    Validates that weight fractions sum to approximately 1.0.
    
    Args:
        fractions: List of weight fractions.
        tolerance: Allowed deviation from 1.0 (default 0.02).
        
    Returns:
        True if sum is within tolerance, False otherwise.
    """
    if not fractions:
        return False
    
    total = sum(fractions)
    return abs(total - 1.0) <= tolerance

def is_valid_smiles(smiles: str) -> bool:
    """
    Checks if a SMILES string is valid using RDKit.
    
    Args:
        smiles: The SMILES string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception as e:
        logger.debug(f"SMILES validation error for '{smiles}': {e}")
        return False

def parse_smiles_to_mol(smiles: str):
    """
    Parses a SMILES string into an RDKit Mol object.
    
    Args:
        smiles: The SMILES string.
        
    Returns:
        RDKit Mol object or None if invalid.
    """
    if not is_valid_smiles(smiles):
        return None
    return Chem.MolFromSmiles(smiles)
