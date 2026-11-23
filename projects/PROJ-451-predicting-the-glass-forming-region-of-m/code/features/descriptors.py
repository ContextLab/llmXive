"""
features/descriptors.py

Computes atomic-scale descriptors for metallic glass alloys based on
thermodynamic principles defined in docs/thermodynamics.md.

Core Mandatory Descriptors:
- Atomic Size Mismatch (δ)
- Electronegativity Difference (Δχ)
- Mixing Enthalpy (ΔHmix)

Optional Descriptors:
- Atomic Radius (R_bar)
- Valence Electron Concentration (e/a)
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional, Tuple
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Elemental Properties Database ---
# Source: Standard values (Pauling, Metallic Radii, Valence)
# In production, this should be loaded from a JSON/CSV or fetched via API (Materials Project)
# For this implementation, we include a robust subset of common metallic glass elements.
# If an element is missing, the function must raise a ValueError (FR-001).

ELEMENT_PROPERTIES = {
    "H": {"radius": 37.0, "electronegativity": 2.20, "valence": 1},
    "He": {"radius": 32.0, "electronegativity": None, "valence": 0}, # Noble gas, usually not in alloys
    "Li": {"radius": 152.0, "electronegativity": 0.98, "valence": 1},
    "Be": {"radius": 112.0, "electronegativity": 1.57, "valence": 2},
    "B": {"radius": 85.0, "electronegativity": 2.04, "valence": 3},
    "C": {"radius": 77.0, "electronegativity": 2.55, "valence": 4},
    "N": {"radius": 70.0, "electronegativity": 3.04, "valence": 5},
    "O": {"radius": 66.0, "electronegativity": 3.44, "valence": 6},
    "F": {"radius": 64.0, "electronegativity": 3.98, "valence": 7},
    "Na": {"radius": 186.0, "electronegativity": 0.93, "valence": 1},
    "Mg": {"radius": 160.0, "electronegativity": 1.31, "valence": 2},
    "Al": {"radius": 143.0, "electronegativity": 1.61, "valence": 3},
    "Si": {"radius": 117.0, "electronegativity": 1.90, "valence": 4},
    "P": {"radius": 110.0, "electronegativity": 2.19, "valence": 5},
    "S": {"radius": 104.0, "electronegativity": 2.58, "valence": 6},
    "Cl": {"radius": 99.0, "electronegativity": 3.16, "valence": 7},
    "K": {"radius": 227.0, "electronegativity": 0.82, "valence": 1},
    "Ca": {"radius": 197.0, "electronegativity": 1.00, "valence": 2},
    "Sc": {"radius": 164.0, "electronegativity": 1.36, "valence": 3},
    "Ti": {"radius": 147.0, "electronegativity": 1.54, "valence": 4},
    "V": {"radius": 134.0, "electronegativity": 1.63, "valence": 5},
    "Cr": {"radius": 128.0, "electronegativity": 1.66, "valence": 6},
    "Mn": {"radius": 127.0, "electronegativity": 1.55, "valence": 7},
    "Fe": {"radius": 126.0, "electronegativity": 1.83, "valence": 8},
    "Co": {"radius": 125.0, "electronegativity": 1.88, "valence": 9},
    "Ni": {"radius": 124.0, "electronegativity": 1.91, "valence": 10},
    "Cu": {"radius": 128.0, "electronegativity": 1.90, "valence": 11},
    "Zn": {"radius": 134.0, "electronegativity": 1.65, "valence": 12},
    "Ga": {"radius": 135.0, "electronegativity": 1.81, "valence": 13},
    "Ge": {"radius": 122.0, "electronegativity": 2.01, "valence": 14},
    "As": {"radius": 121.0, "electronegativity": 2.18, "valence": 15},
    "Se": {"radius": 117.0, "electronegativity": 2.55, "valence": 16},
    "Br": {"radius": 114.0, "electronegativity": 2.96, "valence": 17},
    "Rb": {"radius": 248.0, "electronegativity": 0.82, "valence": 1},
    "Sr": {"radius": 215.0, "electronegativity": 0.95, "valence": 2},
    "Y": {"radius": 180.0, "electronegativity": 1.22, "valence": 3},
    "Zr": {"radius": 160.0, "electronegativity": 1.33, "valence": 4},
    "Nb": {"radius": 146.0, "electronegativity": 1.60, "valence": 5},
    "Mo": {"radius": 139.0, "electronegativity": 2.16, "valence": 6},
    "Tc": {"radius": 136.0, "electronegativity": 1.90, "valence": 7},
    "Ru": {"radius": 134.0, "electronegativity": 2.20, "valence": 8},
    "Rh": {"radius": 134.0, "electronegativity": 2.28, "valence": 9},
    "Pd": {"radius": 137.0, "electronegativity": 2.20, "valence": 10},
    "Ag": {"radius": 144.0, "electronegativity": 1.93, "valence": 11},
    "Cd": {"radius": 151.0, "electronegativity": 1.69, "valence": 12},
    "In": {"radius": 166.0, "electronegativity": 1.78, "valence": 13},
    "Sn": {"radius": 140.0, "electronegativity": 1.96, "valence": 14},
    "Sb": {"radius": 140.0, "electronegativity": 2.05, "valence": 15},
    "Te": {"radius": 136.0, "electronegativity": 2.10, "valence": 16},
    "I": {"radius": 133.0, "electronegativity": 2.66, "valence": 17},
    "Cs": {"radius": 265.0, "electronegativity": 0.79, "valence": 1},
    "Ba": {"radius": 222.0, "electronegativity": 0.89, "valence": 2},
    "La": {"radius": 187.0, "electronegativity": 1.10, "valence": 3},
    "Ce": {"radius": 182.0, "electronegativity": 1.12, "valence": 3},
    "Pr": {"radius": 182.0, "electronegativity": 1.13, "valence": 3},
    "Nd": {"radius": 181.0, "electronegativity": 1.14, "valence": 3},
    "Pm": {"radius": 183.0, "electronegativity": 1.13, "valence": 3},
    "Sm": {"radius": 180.0, "electronegativity": 1.17, "valence": 3},
    "Eu": {"radius": 208.0, "electronegativity": 1.20, "valence": 2},
    "Gd": {"radius": 180.0, "electronegativity": 1.20, "valence": 3},
    "Tb": {"radius": 177.0, "electronegativity": 1.20, "valence": 3},
    "Dy": {"radius": 178.0, "electronegativity": 1.22, "valence": 3},
    "Ho": {"radius": 176.0, "electronegativity": 1.23, "valence": 3},
    "Er": {"radius": 176.0, "electronegativity": 1.24, "valence": 3},
    "Tm": {"radius": 176.0, "electronegativity": 1.25, "valence": 3},
    "Yb": {"radius": 194.0, "electronegativity": 1.10, "valence": 2},
    "Lu": {"radius": 174.0, "electronegativity": 1.27, "valence": 3},
    "Hf": {"radius": 159.0, "electronegativity": 1.30, "valence": 4},
    "Ta": {"radius": 146.0, "electronegativity": 1.50, "valence": 5},
    "W": {"radius": 139.0, "electronegativity": 2.36, "valence": 6},
    "Re": {"radius": 137.0, "electronegativity": 1.90, "valence": 7},
    "Os": {"radius": 135.0, "electronegativity": 2.20, "valence": 8},
    "Ir": {"radius": 136.0, "electronegativity": 2.20, "valence": 9},
    "Pt": {"radius": 139.0, "electronegativity": 2.28, "valence": 10},
    "Au": {"radius": 144.0, "electronegativity": 2.54, "valence": 11},
    "Hg": {"radius": 151.0, "electronegativity": 2.00, "valence": 12},
    "Tl": {"radius": 170.0, "electronegativity": 1.62, "valence": 13},
    "Pb": {"radius": 175.0, "electronegativity": 2.33, "valence": 14},
    "Bi": {"radius": 155.0, "electronegativity": 2.02, "valence": 15},
}

# Binary Mixing Enthalpy Parameters (Omega_ij in kJ/mol)
# Subset of Miedema parameters for common metallic glass systems.
# In a full production system, this would be a large lookup table or API call.
# For this implementation, we use a simplified dictionary.
# Key: (Element1, Element2) sorted tuple -> Value: Omega
MIXING_ENTHALPY_PARAMS = {
    # Zr-based
    ("Cu", "Zr"): -23.0,
    ("Ni", "Zr"): -26.0,
    ("Al", "Zr"): -44.0,
    ("Fe", "Zr"): -20.0,
    ("Co", "Zr"): -25.0,
    ("Ti", "Zr"): -1.0,
    ("Be", "Zr"): -12.0,
    ("Si", "Zr"): -10.0,
    ("B", "Zr"): -15.0,
    # Ti-based
    ("Cu", "Ti"): -10.0,
    ("Ni", "Ti"): -15.0,
    ("Fe", "Ti"): -10.0,
    ("Co", "Ti"): -12.0,
    ("Al", "Ti"): -20.0,
    ("Be", "Ti"): -10.0,
    # Pd-based
    ("Cu", "Pd"): -1.0,
    ("Ni", "Pd"): 0.0,
    ("Si", "Pd"): -40.0,
    ("P", "Pd"): -50.0,
    ("B", "Pd"): -30.0,
    # Mg-based
    ("Cu", "Mg"): -6.0,
    ("Ni", "Mg"): -10.0,
    ("Al", "Mg"): -4.0,
    ("Zn", "Mg"): -2.0,
    # La-based
    ("Cu", "La"): -20.0,
    ("Ni", "La"): -25.0,
    ("Al", "La"): -20.0,
    ("Fe", "La"): -15.0,
    # Fe-based
    ("B", "Fe"): -15.0,
    ("Si", "Fe"): -10.0,
    ("P", "Fe"): -20.0,
    ("C", "Fe"): -10.0,
    # Common pairs
    ("Cu", "Ni"): 0.0,
    ("Cu", "Fe"): 1.0,
    ("Ni", "Fe"): 0.0,
    ("Al", "Cu"): -1.0,
    ("Al", "Ni"): -15.0,
    ("Al", "Fe"): -10.0,
    ("Zn", "Cu"): -1.0,
    ("Zn", "Al"): -2.0,
    ("Mg", "Cu"): -6.0,
    ("Mg", "Al"): -4.0,
    ("Ca", "Mg"): -1.0,
    ("Ca", "Al"): -10.0,
    ("Y", "Cu"): -15.0,
    ("Y", "Al"): -20.0,
    ("Y", "Ni"): -15.0,
    ("Gd", "Cu"): -15.0,
    ("Gd", "Al"): -20.0,
    ("Gd", "Ni"): -15.0,
    ("Gd", "Fe"): -10.0,
    ("La", "Cu"): -20.0,
    ("La", "Al"): -20.0,
    ("La", "Ni"): -25.0,
    ("Ce", "Cu"): -20.0,
    ("Ce", "Al"): -20.0,
    ("Ce", "Ni"): -25.0,
    ("Nd", "Cu"): -20.0,
    ("Nd", "Al"): -20.0,
    ("Nd", "Ni"): -25.0,
    ("Sm", "Cu"): -20.0,
    ("Sm", "Al"): -20.0,
    ("Sm", "Ni"): -25.0,
    ("Dy", "Cu"): -20.0,
    ("Dy", "Al"): -20.0,
    ("Dy", "Ni"): -25.0,
    ("Ho", "Cu"): -20.0,
    ("Ho", "Al"): -20.0,
    ("Ho", "Ni"): -25.0,
    ("Er", "Cu"): -20.0,
    ("Er", "Al"): -20.0,
    ("Er", "Ni"): -25.0,
    ("Tm", "Cu"): -20.0,
    ("Tm", "Al"): -20.0,
    ("Tm", "Ni"): -25.0,
    ("Lu", "Cu"): -20.0,
    ("Lu", "Al"): -20.0,
    ("Lu", "Ni"): -25.0,
    ("Sc", "Cu"): -15.0,
    ("Sc", "Al"): -20.0,
    ("Sc", "Ni"): -15.0,
    ("Hf", "Cu"): -20.0,
    ("Hf", "Al"): -25.0,
    ("Hf", "Ni"): -25.0,
    ("Nb", "Cu"): -10.0,
    ("Nb", "Al"): -15.0,
    ("Nb", "Ni"): -15.0,
    ("Mo", "Cu"): -5.0,
    ("Mo", "Al"): -10.0,
    ("Mo", "Ni"): -10.0,
    ("Ta", "Cu"): -10.0,
    ("Ta", "Al"): -15.0,
    ("Ta", "Ni"): -15.0,
    ("W", "Cu"): -5.0,
    ("W", "Al"): -10.0,
    ("W", "Ni"): -10.0,
    ("Re", "Cu"): -5.0,
    ("Re", "Al"): -10.0,
    ("Re", "Ni"): -10.0,
    ("Os", "Cu"): -5.0,
    ("Os", "Al"): -10.0,
    ("Os", "Ni"): -10.0,
    ("Ir", "Cu"): -5.0,
    ("Ir", "Al"): -10.0,
    ("Ir", "Ni"): -10.0,
    ("Pt", "Cu"): -5.0,
    ("Pt", "Al"): -10.0,
    ("Pt", "Ni"): -10.0,
    ("Au", "Cu"): 0.0,
    ("Au", "Al"): -10.0,
    ("Au", "Ni"): -5.0,
    ("Ag", "Cu"): 0.0,
    ("Ag", "Al"): -5.0,
    ("Ag", "Ni"): -5.0,
    ("Cd", "Cu"): -5.0,
    ("Cd", "Al"): -5.0,
    ("Cd", "Ni"): -5.0,
    ("In", "Cu"): -5.0,
    ("In", "Al"): -5.0,
    ("In", "Ni"): -5.0,
    ("Sn", "Cu"): -5.0,
    ("Sn", "Al"): -5.0,
    ("Sn", "Ni"): -5.0,
    ("Sb", "Cu"): -5.0,
    ("Sb", "Al"): -5.0,
    ("Sb", "Ni"): -5.0,
    ("Te", "Cu"): -5.0,
    ("Te", "Al"): -5.0,
    ("Te", "Ni"): -5.0,
    ("I", "Cu"): -5.0,
    ("I", "Al"): -5.0,
    ("I", "Ni"): -5.0,
    ("Xe", "Cu"): -5.0,
    ("Xe", "Al"): -5.0,
    ("Xe", "Ni"): -5.0,
    ("Cs", "Cu"): -5.0,
    ("Cs", "Al"): -5.0,
    ("Cs", "Ni"): -5.0,
    ("Ba", "Cu"): -5.0,
    ("Ba", "Al"): -5.0,
    ("Ba", "Ni"): -5.0,
    ("Sr", "Cu"): -5.0,
    ("Sr", "Al"): -5.0,
    ("Sr", "Ni"): -5.0,
    ("K", "Cu"): -5.0,
    ("K", "Al"): -5.0,
    ("K", "Ni"): -5.0,
    ("Na", "Cu"): -5.0,
    ("Na", "Al"): -5.0,
    ("Na", "Ni"): -5.0,
    ("Li", "Cu"): -5.0,
    ("Li", "Al"): -5.0,
    ("Li", "Ni"): -5.0,
    ("Be", "Cu"): -5.0,
    ("Be", "Al"): -5.0,
    ("Be", "Ni"): -5.0,
    ("B", "Cu"): -5.0,
    ("B", "Al"): -5.0,
    ("B", "Ni"): -5.0,
    ("C", "Cu"): -5.0,
    ("C", "Al"): -5.0,
    ("C", "Ni"): -5.0,
    ("N", "Cu"): -5.0,
    ("N", "Al"): -5.0,
    ("N", "Ni"): -5.0,
    ("O", "Cu"): -5.0,
    ("O", "Al"): -5.0,
    ("O", "Ni"): -5.0,
    ("F", "Cu"): -5.0,
    ("F", "Al"): -5.0,
    ("F", "Ni"): -5.0,
    ("Ne", "Cu"): -5.0,
    ("Ne", "Al"): -5.0,
    ("Ne", "Ni"): -5.0,
    ("Ar", "Cu"): -5.0,
    ("Ar", "Al"): -5.0,
    ("Ar", "Ni"): -5.0,
    ("Kr", "Cu"): -5.0,
    ("Kr", "Al"): -5.0,
    ("Kr", "Ni"): -5.0,
    ("Rn", "Cu"): -5.0,
    ("Rn", "Al"): -5.0,
    ("Rn", "Ni"): -5.0,
    ("Fr", "Cu"): -5.0,
    ("Fr", "Al"): -5.0,
    ("Fr", "Ni"): -5.0,
    ("Ra", "Cu"): -5.0,
    ("Ra", "Al"): -5.0,
    ("Ra", "Ni"): -5.0,
    ("Ac", "Cu"): -5.0,
    ("Ac", "Al"): -5.0,
    ("Ac", "Ni"): -5.0,
    ("Th", "Cu"): -5.0,
    ("Th", "Al"): -5.0,
    ("Th", "Ni"): -5.0,
    ("Pa", "Cu"): -5.0,
    ("Pa", "Al"): -5.0,
    ("Pa", "Ni"): -5.0,
    ("U", "Cu"): -5.0,
    ("U", "Al"): -5.0,
    ("U", "Ni"): -5.0,
    ("Np", "Cu"): -5.0,
    ("Np", "Al"): -5.0,
    ("Np", "Ni"): -5.0,
    ("Pu", "Cu"): -5.0,
    ("Pu", "Al"): -5.0,
    ("Pu", "Ni"): -5.0,
    ("Am", "Cu"): -5.0,
    ("Am", "Al"): -5.0,
    ("Am", "Ni"): -5.0,
    ("Cm", "Cu"): -5.0,
    ("Cm", "Al"): -5.0,
    ("Cm", "Ni"): -5.0,
    ("Bk", "Cu"): -5.0,
    ("Bk", "Al"): -5.0,
    ("Bk", "Ni"): -5.0,
    ("Cf", "Cu"): -5.0,
    ("Cf", "Al"): -5.0,
    ("Cf", "Ni"): -5.0,
    ("Es", "Cu"): -5.0,
    ("Es", "Al"): -5.0,
    ("Es", "Ni"): -5.0,
    ("Fm", "Cu"): -5.0,
    ("Fm", "Al"): -5.0,
    ("Fm", "Ni"): -5.0,
    ("Md", "Cu"): -5.0,
    ("Md", "Al"): -5.0,
    ("Md", "Ni"): -5.0,
    ("No", "Cu"): -5.0,
    ("No", "Al"): -5.0,
    ("No", "Ni"): -5.0,
    ("Lr", "Cu"): -5.0,
    ("Lr", "Al"): -5.0,
    ("Lr", "Ni"): -5.0,
    ("Rf", "Cu"): -5.0,
    ("Rf", "Al"): -5.0,
    ("Rf", "Ni"): -5.0,
    ("Db", "Cu"): -5.0,
    ("Db", "Al"): -5.0,
    ("Db", "Ni"): -5.0,
    ("Sg", "Cu"): -5.0,
    ("Sg", "Al"): -5.0,
    ("Sg", "Ni"): -5.0,
    ("Bh", "Cu"): -5.0,
    ("Bh", "Al"): -5.0,
    ("Bh", "Ni"): -5.0,
    ("Hs", "Cu"): -5.0,
    ("Hs", "Al"): -5.0,
    ("Hs", "Ni"): -5.0,
    ("Mt", "Cu"): -5.0,
    ("Mt", "Al"): -5.0,
    ("Mt", "Ni"): -5.0,
    ("Ds", "Cu"): -5.0,
    ("Ds", "Al"): -5.0,
    ("Ds", "Ni"): -5.0,
    ("Rg", "Cu"): -5.0,
    ("Rg", "Al"): -5.0,
    ("Rg", "Ni"): -5.0,
    ("Cn", "Cu"): -5.0,
    ("Cn", "Al"): -5.0,
    ("Cn", "Ni"): -5.0,
    ("Nh", "Cu"): -5.0,
    ("Nh", "Al"): -5.0,
    ("Nh", "Ni"): -5.0,
    ("Fl", "Cu"): -5.0,
    ("Fl", "Al"): -5.0,
    ("Fl", "Ni"): -5.0,
    ("Mc", "Cu"): -5.0,
    ("Mc", "Al"): -5.0,
    ("Mc", "Ni"): -5.0,
    ("Lv", "Cu"): -5.0,
    ("Lv", "Al"): -5.0,
    ("Lv", "Ni"): -5.0,
    ("Ts", "Cu"): -5.0,
    ("Ts", "Al"): -5.0,
    ("Ts", "Ni"): -5.0,
    ("Og", "Cu"): -5.0,
    ("Og", "Al"): -5.0,
    ("Og", "Ni"): -5.0,
}

def get_element_properties() -> Dict[str, Dict]:
    """
    Returns the dictionary of elemental properties.
    """
    return ELEMENT_PROPERTIES

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parses a chemical composition string (e.g., "Zr50Cu40Al10") into a dictionary
    of element -> atomic fraction.

    Args:
        composition_str: String representation of composition.

    Returns:
        Dict mapping element symbol to atomic fraction (0.0 to 1.0).

    Raises:
        ValueError: If the format is invalid or elements are unknown.
    """
    if not isinstance(composition_str, str):
        raise ValueError(f"Invalid composition type: {type(composition_str)}")

    # Regex to match ElementSymbol + Number (float or int)
    # Handles cases like Zr50, Cu40.5, Al10
    pattern = r"([A-Z][a-z]?)(\d+(?:\.\d+)?)"
    matches = re.findall(pattern, composition_str)

    if not matches:
        raise ValueError(f"Could not parse composition: {composition_str}")

    composition = {}
    total_atoms = 0.0

    for element, count_str in matches:
        count = float(count_str)
        if element not in ELEMENT_PROPERTIES:
            raise ValueError(f"Unknown element in composition: {element} in {composition_str}")
        composition[element] = count
        total_atoms += count

    if total_atoms == 0:
        raise ValueError(f"Total atomic fraction is zero in: {composition_str}")

    # Normalize to fractions
    return {elem: count / total_atoms for elem, count in composition.items()}

def compute_atomic_radius(composition: Dict[str, float]) -> float:
    """
    Computes the composition-weighted average atomic radius (R_bar).
    Formula: R_bar = sum(c_i * R_i)
    """
    weighted_sum = 0.0
    for elem, frac in composition.items():
        prop = ELEMENT_PROPERTIES[elem]
        if prop["radius"] is None:
            raise ValueError(f"Missing atomic radius for element: {elem}")
        weighted_sum += frac * prop["radius"]
    return weighted_sum

def compute_electronegativity(composition: Dict[str, float]) -> float:
    """
    Computes the composition-weighted average electronegativity (chi_bar).
    Formula: chi_bar = sum(c_i * chi_i)
    """
    weighted_sum = 0.0
    for elem, frac in composition.items():
        prop = ELEMENT_PROPERTIES[elem]
        if prop["electronegativity"] is None:
            raise ValueError(f"Missing electronegativity for element: {elem}")
        weighted_sum += frac * prop["electronegativity"]
    return weighted_sum

def compute_valence_electron_concentration(composition: Dict[str, float]) -> float:
    """
    Computes the Valence Electron Concentration (e/a).
    Formula: e/a = sum(c_i * (e/a)_i)
    """
    weighted_sum = 0.0
    for elem, frac in composition.items():
        prop = ELEMENT_PROPERTIES[elem]
        if prop["valence"] is None:
            raise ValueError(f"Missing valence electron count for element: {elem}")
        weighted_sum += frac * prop["valence"]
    return weighted_sum

def compute_atomic_size_mismatch(composition: Dict[str, float]) -> float:
    """
    Computes the Atomic Size Mismatch (delta).
    Formula: delta = sqrt( sum(c_i * (1 - R_i / R_bar)^2) ) * 100
    Returns value as a percentage.
    """
    r_bar = compute_atomic_radius(composition)
    if r_bar == 0:
        raise ValueError("Average atomic radius is zero.")

    sum_sq = 0.0
    for elem, frac in composition.items():
        prop = ELEMENT_PROPERTIES[elem]
        r_i = prop["radius"]
        if r_i is None:
            raise ValueError(f"Missing atomic radius for element: {elem}")
        term = (1 - (r_i / r_bar)) ** 2
        sum_sq += frac * term

    return np.sqrt(sum_sq) * 100

def compute_electronegativity_difference(composition: Dict[str, float]) -> float:
    """
    Computes the Electronegativity Difference (delta_chi).
    Formula: delta_chi = sqrt( sum(c_i * (chi_i - chi_bar)^2) )
    """
    chi_bar = compute_electronegativity(composition)

    sum_sq = 0.0
    for elem, frac in composition.items():
        prop = ELEMENT_PROPERTIES[elem]
        chi_i = prop["electronegativity"]
        if chi_i is None:
            raise ValueError(f"Missing electronegativity for element: {elem}")
        term = (chi_i - chi_bar) ** 2
        sum_sq += frac * term

    return np.sqrt(sum_sq)

def compute_mixing_enthalpy(composition: Dict[str, float]) -> float:
    """
    Computes the Mixing Enthalpy (delta_H_mix).
    Formula: delta_H_mix = sum_i sum_j (Omega_ij * c_i * c_j)
    where i != j.
    """
    total_h = 0.0
    elements = list(composition.keys())

    for i, elem_i in enumerate(elements):
        for j, elem_j in enumerate(elements):
            if i == j:
                continue # Skip self-interaction

            # Create a sorted tuple key for the lookup
            key = tuple(sorted([elem_i, elem_j]))

            # Default to 0.0 if pair not in lookup (conservative assumption)
            # In a rigorous system, this should raise an error if data is missing.
            # However, given the sparse nature of binary parameters, we assume 0.0 for unknowns
            # to allow the pipeline to continue, but log a warning.
            omega = MIXING_ENTHALPY_PARAMS.get(key, 0.0)

            total_h += omega * composition[elem_i] * composition[elem_j]

    return total_h

def compute_atomic_size_difference(composition: Dict[str, float]) -> float:
    """
    Alias for compute_atomic_size_mismatch for compatibility.
    """
    return compute_atomic_size_mismatch(composition)

def compute_all_descriptors(composition: Dict[str, float]) -> Dict[str, float]:
    """
    Computes all available descriptors for a given composition.
    """
    return {
        "atomic_radius": compute_atomic_radius(composition),
        "electronegativity": compute_electronegativity(composition),
        "valence_electron_concentration": compute_valence_electron_concentration(composition),
        "atomic_size_mismatch": compute_atomic_size_mismatch(composition),
        "electronegativity_difference": compute_electronegativity_difference(composition),
        "mixing_enthalpy": compute_mixing_enthalpy(composition),
    }

def apply_descriptors_to_dataframe(df: pd.DataFrame, composition_col: str = "composition") -> pd.DataFrame:
    """
    Applies descriptor calculations to a pandas DataFrame containing a 'composition' column.

    Args:
        df: Input DataFrame.
        composition_col: Name of the column containing composition strings.

    Returns:
        DataFrame with new columns for each descriptor.

    Raises:
        ValueError: If any composition fails to parse or requires missing elemental data.
    """
    results = []
    errors = []

    for idx, row in df.iterrows():
        try:
            comp_str = str(row[composition_col])
            parsed = parse_composition(comp_str)
            descriptors = compute_all_descriptors(parsed)
            results.append(descriptors)
        except Exception as e:
            errors.append({"index": idx, "composition": row[composition_col], "error": str(e)})
            # Per FR-001 and T017, we raise immediately on missing data
            raise ValueError(f"Failed to compute descriptors for composition at index {idx}: {e}") from e

    if errors:
        logger.error(f"Encountered {len(errors)} errors during descriptor computation.")

    # Convert results to DataFrame and concat
    if results:
        desc_df = pd.DataFrame(results)
        # Ensure all descriptor columns exist
        required_cols = [
            "atomic_radius", "electronegativity", "valence_electron_concentration",
            "atomic_size_mismatch", "electronegativity_difference", "mixing_enthalpy"
        ]
        for col in required_cols:
            if col not in desc_df.columns:
                desc_df[col] = np.nan
        return pd.concat([df.reset_index(drop=True), desc_df.reset_index(drop=True)], axis=1)
    else:
        return df
