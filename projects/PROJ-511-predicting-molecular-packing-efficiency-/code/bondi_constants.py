"""
Bondi van der Waals radii constants (Bondi, 1964).
Values in Angstroms.
"""
from typing import Dict
import math

# Bondi radii in Angstroms
BOND_RADII: Dict[str, float] = {
    'H': 1.20,
    'He': 1.40,
    'Li': 1.82,
    'Be': 1.50, # Approximate
    'B': 2.00,  # Approximate
    'C': 1.70,
    'N': 1.55,
    'O': 1.52,
    'F': 1.47,
    'Ne': 1.54,
    'Na': 2.27,
    'Mg': 1.73,
    'Al': 1.84,
    'Si': 2.10,
    'P': 1.80,
    'S': 1.80,
    'Cl': 1.75,
    'Ar': 1.88,
    'K': 2.75,
    'Ca': 2.31,
    'Sc': 2.11,
    'Ti': 2.00,
    'V': 1.90,
    'Cr': 1.89,
    'Mn': 1.80,
    'Fe': 1.94,
    'Co': 1.92,
    'Ni': 1.93,
    'Cu': 1.72,
    'Zn': 1.31, # Often cited as 1.31 or 1.40, using 1.31 per some extensions
    'Ga': 1.87,
    'Ge': 2.11,
    'As': 1.85,
    'Se': 1.90,
    'Br': 1.85,
    'Kr': 2.02,
    'Rb': 3.03,
    'Sr': 2.49,
    'Y': 2.07,
    'Zr': 2.06,
    'Nb': 2.08,
    'Mo': 2.05,
    'Tc': 2.00,
    'Ru': 2.00,
    'Rh': 1.95,
    'Pd': 1.95,
    'Ag': 1.72,
    'Cd': 1.90,
    'In': 1.93,
    'Sn': 2.01,
    'Sb': 2.06,
    'Te': 2.06,
    'I': 1.98,
    'Xe': 2.16,
    'Cs': 3.43,
    'Ba': 2.68,
    'La': 2.35,
    'Ce': 2.30,
    'Pr': 2.28,
    'Nd': 2.26,
    'Pm': 2.24,
    'Sm': 2.22,
    'Eu': 2.20,
    'Gd': 2.18,
    'Tb': 2.16,
    'Dy': 2.14,
    'Ho': 2.12,
    'Er': 2.10,
    'Tm': 2.08,
    'Yb': 2.06,
    'Lu': 2.04,
    'Hf': 2.11,
    'Ta': 2.10,
    'W': 2.10,
    'Re': 2.08,
    'Os': 2.06,
    'Ir': 2.04,
    'Pt': 2.02,
    'Au': 1.98,
    'Hg': 1.80,
    'Tl': 1.90,
    'Pb': 1.87,
    'Bi': 2.07,
    'Po': 2.00,
    'At': 2.00,
    'Rn': 2.20
}

def calculate_vdw_volume(radii: float) -> float:
    """
    Calculate the volume of a sphere given its radius.
    V = 4/3 * pi * r^3
    """
    return (4.0 / 3.0) * math.pi * (radii ** 3)
