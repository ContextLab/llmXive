from typing import Union, List, Tuple, Optional
from rdkit import Chem
from rdkit.Chem import Descriptors
import logging

logger = logging.getLogger(__name__)

def celsius_to_kelvin(temp_c: float) -> float:
    """Convert temperature from Celsius to Kelvin."""
    return temp_c + 273.15

def pascal_to_gpa(pressure_pa: float) -> float:
    """Convert pressure/stress from Pascal to GPa."""
    return pressure_pa * 1e-9

def validate_weight_fractions(weights: List[float], tolerance: float = 0.02) -> bool:
    """
    Validate that weight fractions sum to approximately 1.0.
    
    Args:
        weights: List of weight fractions
        tolerance: Allowed deviation from 1.0
        
    Returns:
        True if sum is within tolerance, False otherwise
    """
    if not weights:
        return False
    
    total = sum(weights)
    return abs(total - 1.0) <= tolerance

def is_valid_smiles(smiles: str) -> bool:
    """
    Validate SMILES string using RDKit.
    
    Args:
        smiles: SMILES string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not smiles or not isinstance(smiles, str):
        return False
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception as e:
        logger.warning(f"SMILES validation failed for '{smiles}': {e}")
        return False

def parse_smiles_to_mol(smiles: str):
    """
    Parse SMILES string to RDKit Mol object.
    
    Args:
        smiles: SMILES string
        
    Returns:
        RDKit Mol object or None if parsing fails
    """
    if not is_valid_smiles(smiles):
        return None
    
    return Chem.MolFromSmiles(smiles)
