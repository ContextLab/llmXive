"""
Constants and utility functions for unit conversion and polymer classification.
"""
from typing import Dict, Any, Callable
from utils.errors import DataInsufficientError
import re

# Unit conversion factors to Barrer (1 Barrer = 10^-10 cm3(STP)·cm / (cm2·s·cmHg))
# Common units found in literature:
# GPU: Gas Permeation Unit (1 GPU = 10^-6 cm3(STP) / (cm2·s·cmHg)) -> 1 GPU = 10,000 Barrer
# Barrer: 1 Barrer
# mol/(m·s·Pa): SI unit. 1 Barrer ≈ 3.348e-16 mol/(m·s·Pa)

UNIT_TO_BARRER = {
    "barrer": 1.0,
    "gpu": 10000.0,
    "gpu (10^-6 cm3 cm cm-2 s-1 cmHg-1)": 10000.0,
    "mol/(m s pa)": 1.0 / 3.348e-16, # Approximate conversion factor
    "mol m-1 s-1 pa-1": 1.0 / 3.348e-16,
    "cm3 (STP) cm / (cm2 s cmHg)": 1.0, # Explicit Barrer definition
}

def convert_permeability_to_barrer(value: float, unit: str) -> float:
    """
    Converts a permeability value to Barrer.
    
    Args:
        value: The permeability value.
        unit: The unit string.
        
    Returns:
        The value in Barrer.
        
    Raises:
        ValueError: If the unit is unknown.
    """
    if pd.isna(value):
        return None
        
    unit_lower = unit.lower().strip()
    if unit_lower not in UNIT_TO_BARRER:
        # Try to find a partial match
        matched = False
        for known_unit, factor in UNIT_TO_BARRER.items():
            if known_unit in unit_lower or unit_lower in known_unit:
                return value * factor
        
        raise ValueError(f"Unknown permeability unit: {unit}")
    
    return value * UNIT_TO_BARRER[unit_lower]

# Dictionary mapping SMILES substructures to polymer class names
# Used for imputation logic when SMILES is available but class is missing
SMILES_TO_CLASS = {
    "c1ccccc1": "Polystyrene", # Benzene ring
    "C=O": "Polyimide", # Carbonyl in imide context (simplified)
    "N": "Polyamide", # Amine/Amide context
    "O": "Polyether", # Ether linkage
    "S(=O)(=O)": "Polysulfone", # Sulfone group
    "c1ccccc1O": "Phenolic", # Phenol group
    "CC(C)(C)": "Polyisobutylene", # Tertiary butyl
    "Cl": "Polyvinyl chloride", # Chlorine
    "F": "PTFE", # Fluorine
}

def get_polymer_class_from_smiles(smiles: str) -> str:
    """
    Derives a polymer class name from a SMILES string using substructure lookup.
    Falls back to 'Unknown' if no match is found.
    """
    if pd.isna(smiles) or not smiles:
        return "Unknown"
    
    for substructure, class_name in SMILES_TO_CLASS.items():
        if substructure in smiles:
            return class_name
    
    return "Unknown"

# Import pandas here to avoid circular imports if this file is imported early
# but we need it for pd.isna check. 
# Since this is a utility file, we can import it at the top or inside the function.
# To avoid circular dependency with utils.errors which might not need pandas:
try:
    import pandas as pd
except ImportError:
    # Fallback if pandas not available (should not happen in this project)
    def pd_isna(val):
        return val is None
    pd = type('pd', (), {'isna': pd_isna})()
