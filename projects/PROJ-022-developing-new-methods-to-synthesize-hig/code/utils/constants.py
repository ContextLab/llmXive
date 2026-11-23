from typing import Dict, Any, Callable
from utils.errors import DataInsufficientError
import re

# Unit conversion factors
# 1 Barrer = 10^-10 (cm^3 (STP) cm) / (cm^2 s cmHg)
# Common conversions handled in specific modules, but constants defined here for reference

# Random seed for reproducibility
RANDOM_SEED = 42

# Mapping of SMILES substructures to polymer class names
# Used for imputation lookup logic (T006b)
SMILES_TO_POLYMER_CLASS: Dict[str, str] = {
    "c1ccccc1": "Polystyrene",
    "C1CCCCC1": "Cycloaliphatic",
    "O=C(O)": "Carboxylic Acid",
    "N": "Amine",
    "C=O": "Carbonyl",
    "c1ccc(O)cc1": "Phenol",
    "CC(=O)O": "Acetate",
    # Add more specific mappings as needed based on literature
}

def convert_permeability_to_barrer(value: float, unit: str) -> float:
    """Convert permeability value to Barrer."""
    # Placeholder for actual conversion logic if needed
    return value

def get_polymer_class_from_smiles(smiles: str) -> str:
    """
    Attempt to infer polymer class from SMILES string using simple substructure matching.
    Returns 'Unknown' if no match is found.
    """
    for substructure, poly_class in SMILES_TO_POLYMER_CLASS.items():
        if substructure in smiles:
            return poly_class
    return "Unknown"
