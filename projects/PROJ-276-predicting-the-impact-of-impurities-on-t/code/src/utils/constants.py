"""
Constants for the MgB2 Impurity Impact Prediction Pipeline.

This module provides atomic weights, unit conversion factors, and
VIF threshold constants used throughout the project.
"""

# Atomic Weights (g/mol)
# Source: IUPAC standard atomic weights
ATOMIC_WEIGHTS = {
    'H': 1.008,
    'He': 4.0026,
    'Li': 6.94,
    'Be': 9.0122,
    'B': 10.81,
    'C': 12.011,
    'N': 14.007,
    'O': 15.999,
    'F': 18.998,
    'Ne': 20.180,
    'Na': 22.990,
    'Mg': 24.305,
    'Al': 26.982,
    'Si': 28.085,
    'P': 30.974,
    'S': 32.06,
    'Cl': 35.45,
    'Ar': 39.948,
    'K': 39.098,
    'Ca': 40.078,
    'Sc': 44.956,
    'Ti': 47.867,
    'V': 50.942,
    'Cr': 51.996,
    'Mn': 54.938,
    'Fe': 55.845,
    'Co': 58.933,
    'Ni': 58.693,
    'Cu': 63.546,
    'Zn': 65.38,
    'Ga': 69.723,
    'Ge': 72.630,
    'As': 74.922,
    'Se': 78.971,
    'Br': 79.904,
    'Kr': 83.798,
    'Rb': 85.468,
    'Sr': 87.62,
    'Y': 88.906,
    'Zr': 91.224,
    'Nb': 92.906,
    'Mo': 95.95,
    'Tc': 98,
    'Ru': 101.07,
    'Rh': 102.91,
    'Pd': 106.42,
    'Ag': 107.87,
    'Cd': 112.41,
    'In': 114.82,
    'Sn': 118.71,
    'Sb': 121.76,
    'Te': 127.60,
    'I': 126.90,
    'Xe': 131.29,
    'Cs': 132.91,
    'Ba': 137.33,
    'La': 138.91,
    'Ce': 140.12,
    'Pr': 140.91,
    'Nd': 144.24,
    'Pm': 145,
    'Sm': 150.36,
    'Eu': 151.96,
    'Gd': 157.25,
    'Tb': 158.93,
    'Dy': 162.50,
    'Ho': 164.93,
    'Er': 167.26,
    'Tm': 168.93,
    'Yb': 173.05,
    'Lu': 174.97,
    'Hf': 178.49,
    'Ta': 180.95,
    'W': 183.84,
    'Re': 186.21,
    'Os': 190.23,
    'Ir': 192.22,
    'Pt': 195.08,
    'Au': 196.97,
    'Hg': 200.59,
    'Tl': 204.38,
    'Pb': 207.2,
    'Bi': 208.98,
    'Po': 209,
    'At': 210,
    'Rn': 222,
    'Fr': 223,
    'Ra': 226,
    'Ac': 227,
    'Th': 232.04,
    'Pa': 231.04,
    'U': 238.03,
    'Np': 237,
    'Pu': 244,
    'Am': 243,
    'Cm': 247,
    'Bk': 247,
    'Cf': 251,
    'Es': 252,
    'Fm': 257,
    'Md': 258,
    'No': 259,
    'Lr': 266,
    'Rf': 267,
    'Db': 268,
    'Sg': 269,
    'Bh': 270,
    'Hs': 277,
    'Mt': 278,
    'Ds': 281,
    'Rg': 282,
    'Cn': 285,
    'Nh': 286,
    'Fl': 289,
    'Mc': 290,
    'Lv': 293,
    'Ts': 294,
    'Og': 294,
}

# Unit Conversion Factors
KELVIN_TO_CELSIUS = 273.15
CELSIUS_TO_KELVIN = 273.15
GPA_TO_PA = 1e9
PA_TO_GPA = 1e-9
MEV_TO_EV = 1e6
EV_TO_MEV = 1e-6

# VIF Threshold Constants
# Established benchmarks for Variance Inflation Factor
VIF_THRESHOLD_LOW = 5.0   # Below this: no multicollinearity concern
VIF_THRESHOLD_HIGH = 10.0 # Above this: severe multicollinearity

# Data Processing Constants
SYNTHESIS_RANGE_DEFAULT = 0.05  # Default uncertainty for synthesis ranges
NULL_VALUE_THRESHOLD = 0.5      # Threshold for null value percentage in validation

def get_atomic_weight(element: str) -> float:
    """
    Retrieve the atomic weight of a given element.

    Args:
        element: Chemical symbol (e.g., 'Mg', 'B')

    Returns:
        Atomic weight in g/mol

    Raises:
        KeyError: If element is not found in ATOMIC_WEIGHTS
    """
    if element not in ATOMIC_WEIGHTS:
        raise KeyError(f"Element '{element}' not found in atomic weights database")
    return ATOMIC_WEIGHTS[element]
