"""
Constants for the MgB2 Impurity Impact Prediction Pipeline.

This module provides atomic weights, unit conversion factors, and
statistical thresholds (VIF) required for data preprocessing and modeling.
"""

# Atomic Weights (g/mol)
# Source: IUPAC Standard Atomic Weights (rounded to 4 decimal places)
ATOMIC_WEIGHTS = {
    "H": 1.0080,
    "He": 4.0026,
    "Li": 6.9400,
    "Be": 9.0122,
    "B": 10.8100,
    "C": 12.0110,
    "N": 14.0070,
    "O": 15.9990,
    "F": 18.9980,
    "Ne": 20.1800,
    "Na": 22.9900,
    "Mg": 24.3050,
    "Al": 26.9820,
    "Si": 28.0850,
    "P": 30.9740,
    "S": 32.0600,
    "Cl": 35.4500,
    "K": 39.0980,
    "Ca": 40.0780,
    "Sc": 44.9560,
    "Ti": 47.8670,
    "V": 50.9420,
    "Cr": 51.9960,
    "Mn": 54.9380,
    "Fe": 55.8450,
    "Co": 58.9330,
    "Ni": 58.6930,
    "Cu": 63.5460,
    "Zn": 65.3800,
    "Ga": 69.7230,
    "Ge": 72.6300,
    "As": 74.9220,
    "Se": 78.9710,
    "Br": 79.9040,
    "Kr": 83.7980,
    "Rb": 85.4680,
    "Sr": 87.6200,
    "Y": 88.9060,
    "Zr": 91.2240,
    "Nb": 92.9060,
    "Mo": 95.9500,
    "Tc": 98.0000,
    "Ru": 101.0700,
    "Rh": 102.9100,
    "Pd": 106.4200,
    "Ag": 107.8700,
    "Cd": 112.4100,
    "In": 114.8200,
    "Sn": 118.7100,
    "Sb": 121.7600,
    "Te": 127.6000,
    "I": 126.9000,
    "Xe": 131.2900,
    "Cs": 132.9100,
    "Ba": 137.3300,
    "La": 138.9100,
    "Ce": 140.1200,
    "Pr": 140.9100,
    "Nd": 144.2400,
    "Pm": 145.0000,
    "Sm": 150.3600,
    "Eu": 151.9600,
    "Gd": 157.2500,
    "Tb": 158.9300,
    "Dy": 162.5000,
    "Ho": 164.9300,
    "Er": 167.2600,
    "Tm": 168.9300,
    "Yb": 173.0500,
    "Lu": 174.9700,
    "Hf": 178.4900,
    "Ta": 180.9500,
    "W": 183.8400,
    "Re": 186.2100,
    "Os": 190.2300,
    "Ir": 192.2200,
    "Pt": 195.0800,
    "Au": 196.9700,
    "Hg": 200.5900,
    "Tl": 204.3800,
    "Pb": 207.2000,
    "Bi": 208.9800,
    "Th": 232.0400,
    "U": 238.0300,
}

# Unit Conversion Factors
# Temperature: Kelvin to Celsius (offset), though we primarily work in Kelvin
KELVIN_TO_CELSIUS_OFFSET = 273.15
CELSIUS_TO_KELVIN_OFFSET = 273.15

# Pressure: GPa to various units
# 1 GPa = 10,000 bar
# 1 GPa = 1,000 MPa
# 1 GPa = 10^9 Pa
GPA_TO_PASCAL = 1e9
GPA_TO_BAR = 10000.0
GPA_TO_MPA = 1000.0

# Statistical Thresholds
# Variance Inflation Factor (VIF) thresholds for multicollinearity
# Source: Standard statistical benchmarks (e.g., Hair et al., Montgomery et al.)
# VIF < 5: No multicollinearity
# 5 <= VIF < 10: Moderate multicollinearity
# VIF >= 10: Severe multicollinearity (often used as the cutoff for removal)
# For this project, we use a conservative threshold of 5.0 as per spec FR-004
VIF_THRESHOLD_CONSERVATIVE = 5.0
VIF_THRESHOLD_STRICT = 10.0

# Data Processing Constants
# Minimum number of samples required for a feature to be considered in modeling
MIN_FEATURE_SAMPLES = 10

# Default value for missing data imputation (if not handled by midpoint logic)
DEFAULT_IMPUTATION_VALUE = 0.0

# Impurity elements commonly found in MgB2 studies (subset of atomic weights)
# Used for quick validation of impurity columns
COMMON_IMPURITY_ELEMENTS = [
    "C", "Si", "Al", "Ti", "Cr", "Mn", "Fe", "Co", "Ni", "Cu",
    "Zr", "Nb", "Y", "Ca", "Sc", "V"
]

def get_atomic_weight(element_symbol: str) -> float:
    """
    Retrieve the atomic weight for a given element symbol.

    Args:
        element_symbol: The chemical symbol (e.g., 'Mg', 'B').

    Returns:
        The atomic weight in g/mol.

    Raises:
        KeyError: If the element symbol is not found in the table.
    """
    if element_symbol not in ATOMIC_WEIGHTS:
        raise KeyError(f"Atomic weight not found for element: {element_symbol}")
    return ATOMIC_WEIGHTS[element_symbol]
