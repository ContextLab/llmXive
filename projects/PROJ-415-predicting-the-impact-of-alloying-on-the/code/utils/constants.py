# code/utils/constants.py
"""
Versioned periodic table data for alloying impact analysis.

This module provides Metallic Radii (pm) and Electronegativity (Pauling scale)
for elements relevant to FCC metal diffusion studies.

Version: 1.0.0
Sources: 
  - Radii: Kittel, C. (2005). Introduction to Solid State Physics.
  - Electronegativity: Pauling, L. (1960). The Nature of the Chemical Bond.
"""

from typing import Dict, Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class ElementData:
    """Data container for a single element's properties."""
    symbol: str
    name: str
    metallic_radius_pm: float
    electronegativity: float

# Versioned data dictionary
# Keys are element symbols (uppercase)
PERIODIC_TABLE: Dict[str, ElementData] = {
    "H":  ElementData("H",  "Hydrogen",     37.0,  2.20),
    "B":  ElementData("B",  "Boron",        87.0,  2.04),
    "C":  ElementData("C",  "Carbon",       70.0,  2.55),
    "N":  ElementData("N",  "Nitrogen",     71.0,  3.04),
    "O":  ElementData("O",  "Oxygen",       66.0,  3.44),
    "F":  ElementData("F",  "Fluorine",     64.0,  3.98),
    "Na": ElementData("Na", "Sodium",       186.0, 0.93),
    "Mg": ElementData("Mg", "Magnesium",    160.0, 1.31),
    "Al": ElementData("Al", "Aluminum",     143.0, 1.61),
    "Si": ElementData("Si", "Silicon",      117.0, 1.90),
    "P":  ElementData("P",  "Phosphorus",   110.0, 2.19),
    "S":  ElementData("S",  "Sulfur",       104.0, 2.58),
    "Cl": ElementData("Cl", "Chlorine",     99.0,  3.16),
    "K":  ElementData("K",  "Potassium",    227.0, 0.82),
    "Ca": ElementData("Ca", "Calcium",      197.0, 1.00),
    "Sc": ElementData("Sc", "Scandium",     162.0, 1.36),
    "Ti": ElementData("Ti", "Titanium",     147.0, 1.54),
    "V":  ElementData("V",  "Vanadium",     134.0, 1.63),
    "Cr": ElementData("Cr", "Chromium",     128.0, 1.66),
    "Mn": ElementData("Mn", "Manganese",    127.0, 1.55),
    "Fe": ElementData("Fe", "Iron",         126.0, 1.83),
    "Co": ElementData("Co", "Cobalt",       125.0, 1.88),
    "Ni": ElementData("Ni", "Nickel",       124.0, 1.91),
    "Cu": ElementData("Cu", "Copper",       128.0, 1.90),
    "Zn": ElementData("Zn", "Zinc",         134.0, 1.65),
    "Ga": ElementData("Ga", "Gallium",      135.0, 1.81),
    "Ge": ElementData("Ge", "Germanium",    122.0, 2.01),
    "As": ElementData("As", "Arsenic",      119.0, 2.18),
    "Se": ElementData("Se", "Selenium",     116.0, 2.55),
    "Br": ElementData("Br", "Bromine",      114.0, 2.96),
    "Rb": ElementData("Rb", "Rubidium",     248.0, 0.82),
    "Sr": ElementData("Sr", "Strontium",    215.0, 0.95),
    "Y":  ElementData("Y",  "Yttrium",      180.0, 1.22),
    "Zr": ElementData("Zr", "Zirconium",    160.0, 1.33),
    "Nb": ElementData("Nb", "Niobium",      146.0, 1.60),
    "Mo": ElementData("Mo", "Molybdenum",   139.0, 2.16),
    "Tc": ElementData("Tc", "Technetium",   136.0, 1.90),
    "Ru": ElementData("Ru", "Ruthenium",    134.0, 2.20),
    "Rh": ElementData("Rh", "Rhodium",      134.0, 2.28),
    "Pd": ElementData("Pd", "Palladium",    137.0, 2.20),
    "Ag": ElementData("Ag", "Silver",       144.0, 1.93),
    "Cd": ElementData("Cd", "Cadmium",      151.0, 1.69),
    "In": ElementData("In", "Indium",       166.0, 1.78),
    "Sn": ElementData("Sn", "Tin",          140.0, 1.96),
    "Sb": ElementData("Sb", "Antimony",     140.0, 2.05),
    "Te": ElementData("Te", "Tellurium",    136.0, 2.10),
    "I":  ElementData("I",  "Iodine",       133.0, 2.66),
    "Cs": ElementData("Cs", "Cesium",       265.0, 0.79),
    "Ba": ElementData("Ba", "Barium",       222.0, 0.89),
    "La": ElementData("La", "Lanthanum",    187.0, 1.10),
    "Ce": ElementData("Ce", "Cerium",       182.0, 1.12),
    "Pr": ElementData("Pr", "Praseodymium", 182.0, 1.13),
    "Nd": ElementData("Nd", "Neodymium",    181.0, 1.14),
    "Sm": ElementData("Sm", "Samarium",     180.0, 1.17),
    "Eu": ElementData("Eu", "Europium",     208.0, 1.20),
    "Gd": ElementData("Gd", "Gadolinium",   180.0, 1.20),
    "Tb": ElementData("Tb", "Terbium",      177.0, 1.20),
    "Dy": ElementData("Dy", "Dysprosium",   177.0, 1.22),
    "Ho": ElementData("Ho", "Holmium",      176.0, 1.23),
    "Er": ElementData("Er", "Erbium",       175.0, 1.24),
    "Tm": ElementData("Tm", "Thulium",      174.0, 1.25),
    "Yb": ElementData("Yb", "Ytterbium",    194.0, 1.10),
    "Lu": ElementData("Lu", "Lutetium",     173.0, 1.27),
    "Hf": ElementData("Hf", "Hafnium",      159.0, 1.30),
    "Ta": ElementData("Ta", "Tantalum",     146.0, 1.50),
    "W":  ElementData("W",  "Tungsten",     139.0, 2.36),
    "Re": ElementData("Re", "Rhenium",      137.0, 1.90),
    "Os": ElementData("Os", "Osmium",       135.0, 2.20),
    "Ir": ElementData("Ir", "Iridium",      136.0, 2.20),
    "Pt": ElementData("Pt", "Platinum",     139.0, 2.28),
    "Au": ElementData("Au", "Gold",         144.0, 2.54),
    "Hg": ElementData("Hg", "Mercury",      151.0, 2.00),
    "Tl": ElementData("Tl", "Thallium",     170.0, 1.62),
    "Pb": ElementData("Pb", "Lead",         175.0, 2.33),
    "Bi": ElementData("Bi", "Bismuth",      155.0, 2.02),
    "Th": ElementData("Th", "Thorium",      180.0, 1.30),
    "Pa": ElementData("Pa", "Protactinium", 163.0, 1.50),
    "U":  ElementData("U",  "Uranium",      156.0, 1.38),
}

def get_metallic_radius(symbol: str) -> Optional[float]:
    """
    Retrieve the metallic radius (in pm) for a given element symbol.
    
    Args:
        symbol: The chemical symbol (e.g., 'Ni', 'Fe').
        
    Returns:
        The metallic radius in picometers, or None if the element is not found.
    """
    data = PERIODIC_TABLE.get(symbol.upper())
    return data.metallic_radius_pm if data else None

def get_electronegativity(symbol: str) -> Optional[float]:
    """
    Retrieve the Pauling electronegativity for a given element symbol.
    
    Args:
        symbol: The chemical symbol (e.g., 'Ni', 'Fe').
        
    Returns:
        The electronegativity value, or None if the element is not found.
    """
    data = PERIODIC_TABLE.get(symbol.upper())
    return data.electronegativity if data else None
