"""
Constants for the MgB2 Impurity Impact Prediction Pipeline.

This module provides atomic weights, unit conversion factors, and
established benchmark thresholds for data processing and modeling.
"""

# ---------------------------------------------------------------------
# Atomic Weights (g/mol)
# Source: IUPAC Periodic Table of Elements (Standard Atomic Weights)
# ---------------------------------------------------------------------
ATOMIC_WEIGHTS = {
    "H": 1.008,
    "He": 4.0026,
    "Li": 6.94,
    "Be": 9.0122,
    "B": 10.81,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "F": 18.998,
    "Ne": 20.180,
    "Na": 22.990,
    "Mg": 24.305,
    "Al": 26.982,
    "Si": 28.085,
    "P": 30.974,
    "S": 32.06,
    "Cl": 35.45,
    "Ar": 39.948,
    "K": 39.098,
    "Ca": 40.078,
    "Sc": 44.956,
    "Ti": 47.867,
    "V": 50.942,
    "Cr": 51.996,
    "Mn": 54.938,
    "Fe": 55.845,
    "Co": 58.933,
    "Ni": 58.693,
    "Cu": 63.546,
    "Zn": 65.38,
    "Ga": 69.723,
    "Ge": 72.630,
    "As": 74.922,
    "Se": 78.971,
    "Br": 79.904,
    "Kr": 83.798,
    "Rb": 85.468,
    "Sr": 87.62,
    "Y": 88.906,
    "Zr": 91.224,
    "Nb": 92.906,
    "Mo": 95.95,
    "Tc": 98.0,
    "Ru": 101.07,
    "Rh": 102.91,
    "Pd": 106.42,
    "Ag": 107.87,
    "Cd": 112.41,
    "In": 114.82,
    "Sn": 118.71,
    "Sb": 121.76,
    "Te": 127.60,
    "I": 126.90,
    "Xe": 131.29,
    "Cs": 132.91,
    "Ba": 137.33,
    "La": 138.91,
    "Ce": 140.12,
    "Pr": 140.91,
    "Nd": 144.24,
    "Pm": 145.0,
    "Sm": 150.36,
    "Eu": 151.96,
    "Gd": 157.25,
    "Tb": 158.93,
    "Dy": 162.50,
    "Ho": 164.93,
    "Er": 167.26,
    "Tm": 168.93,
    "Yb": 173.05,
    "Lu": 174.97,
    "Hf": 178.49,
    "Ta": 180.95,
    "W": 183.84,
    "Re": 186.21,
    "Os": 190.23,
    "Ir": 192.22,
    "Pt": 195.08,
    "Au": 196.97,
    "Hg": 200.59,
    "Tl": 204.38,
    "Pb": 207.2,
    "Bi": 208.98,
    "Th": 232.04,
    "U": 238.03,
}

# ---------------------------------------------------------------------
# Unit Conversion Factors
# ---------------------------------------------------------------------
# Temperature: Kelvin to Celsius
K_TO_C = -273.15
# Temperature: Celsius to Kelvin
C_TO_K = 273.15

# Pressure: GPa to atm (approximate)
GPA_TO_ATM = 9.86923
# Pressure: atm to GPa
ATM_TO_GPA = 0.101325

# ---------------------------------------------------------------------
# VIF (Variance Inflation Factor) Thresholds
# ---------------------------------------------------------------------
# Established benchmarks for multicollinearity detection
# Values below this threshold are considered acceptable
VIF_THRESHOLD_ACCEPTABLE = 5.0
# Values above this threshold indicate severe multicollinearity
VIF_THRESHOLD_SEVERE = 10.0

# ---------------------------------------------------------------------
# Data Processing Constants
# ---------------------------------------------------------------------
# Minimum number of samples required in a bin for stratification
MIN_SAMPLES_PER_BIN = 10
# Default value for missing impurity percentage (treated as 0)
DEFAULT_IMPURITY_PCT = 0.0

def get_atomic_weight(element_symbol: str) -> float:
    """
    Retrieve the atomic weight for a given element symbol.

    Args:
        element_symbol: The chemical symbol (e.g., 'Mg', 'B', 'C').

    Returns:
        The atomic weight in g/mol.

    Raises:
        KeyError: If the element symbol is not found in the database.
    """
    if element_symbol not in ATOMIC_WEIGHTS:
        raise KeyError(f"Atomic weight for element '{element_symbol}' not found.")
    return ATOMIC_WEIGHTS[element_symbol]
