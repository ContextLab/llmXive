"""
Physical Constants Module for Born Model Calculations.

This module provides fundamental physical constants and unit conversion factors
required for the Born equation and solvation energy calculations. All values
are sourced from NIST (National Institute of Standards and Technology) and
CRC Handbook of Chemistry and Physics, with citations provided.

Precision is maintained to appropriate significant figures for thermodynamic
calculations (typically 6-9 significant digits).
"""

# NIST Reference: https://physics.nist.gov/cuu/Constants/
# CRC Handbook of Chemistry and Physics, 104th Edition (2023)

# Fundamental Physical Constants (SI Units)
# Values from NIST 2018 CODATA recommended values

# Speed of light in vacuum (m/s)
C_SPEED_OF_LIGHT = 299_792_458.0  # Exact by definition

# Vacuum permittivity (F/m or C²/(J·m))
# ε₀ = 1 / (μ₀ * c²) where μ₀ is vacuum permeability
EPSILON_0 = 8.854_187_8128e-12  # F/m (NIST 2018, uncertainty 1.3e-20)
EPSILON_0_CITATION = "NIST 2018 CODATA; CRC Handbook 104th Ed."

# Elementary charge (C)
E_ELEMENTARY_CHARGE = 1.602_176_634e-19  # Exact by definition (SI redefinition 2019)
E_CITATION = "NIST 2018 CODATA (exact by definition)"

# Avogadro constant (mol⁻¹)
N_A = 6.022_140_76e23  # Exact by definition (SI redefinition 2019)
N_A_CITATION = "NIST 2018 CODATA (exact by definition)"

# Boltzmann constant (J/K)
K_B = 1.380_649e-23  # Exact by definition (SI redefinition 2019)
K_B_CITATION = "NIST 2018 CODATA (exact by definition)"

# Gas constant (J/(mol·K)) = N_A * K_B
R_GAS_CONSTANT = 8.314_462_618  # J/(mol·K)
R_CITATION = "Calculated from NIST 2018 CODATA constants (exact)"

# Faraday constant (C/mol) = N_A * e
F_FARADAY = 96_485.332_12  # C/mol
F_CITATION = "Calculated from NIST 2018 CODATA constants (exact)"

# Planck constant (J·s) - included for completeness
H_PLANCK = 6.626_070_15e-34  # J·s (exact by definition)
H_CITATION = "NIST 2018 CODATA (exact by definition)"

# Unit Conversion Factors
# These are exact conversion factors between common units

# Length conversions
ANGSTROM_TO_METER = 1e-10  # 1 Å = 1e-10 m (exact)
NM_TO_METER = 1e-9  # 1 nm = 1e-9 m (exact)
METER_TO_ANGSTROM = 1e10  # 1 m = 1e10 Å (exact)

# Energy conversions
JOULE_TO_KCAL = 1 / 4184.0  # 1 cal = 4.184 J (exact, thermochemical calorie)
KCAL_TO_JOULE = 4184.0  # 1 kcal = 4184 J (exact, thermochemical calorie)
JOULE_TO_KJ = 1e-3  # 1 kJ = 1000 J (exact)
KJ_TO_JOULE = 1000.0  # 1 kJ = 1000 J (exact)
EV_TO_JOULE = 1.602_176_634e-19  # 1 eV in J (exact, by definition of e)
KJ_PER_MOL_TO_JOULE_PER_MOLE = 1000.0  # 1 kJ/mol = 1000 J/mol (exact)

# Temperature conversions
CELSIUS_TO_KELVIN_OFFSET = 273.15  # T(K) = T(°C) + 273.15 (exact)

# Dielectric constant (dimensionless, no conversion needed)
# ε_r (relative permittivity) is unitless

# Standard reference conditions
STANDARD_TEMPERATURE_KELVIN = 298.15  # 25°C in Kelvin (standard laboratory temp)
STANDARD_PRESSURE_PASCAL = 101_325.0  # 1 atm in Pa (exact)

# Water dielectric constant at standard conditions (approximate, varies with T)
# Source: CRC Handbook, varies ~78.5 at 25°C
WATER_DIELECTRIC_25C = 78.36  # Dimensionless (CRC 104th Ed, Table 6.14)
WATER_DIELECTRIC_CITATION = "CRC Handbook 104th Ed., Table 6.14"

# Helper functions for unit conversions
def angstroms_to_meters(radius_angstrom: float) -> float:
    """
    Convert radius from Angstroms to meters.

    Args:
        radius_angstrom: Radius in Angstroms (Å)

    Returns:
        Radius in meters (m)

    Note:
        Conversion factor is exact (1 Å = 1e-10 m)
    """
    return radius_angstrom * ANGSTROM_TO_METER

def meters_to_angstroms(radius_meters: float) -> float:
    """
    Convert radius from meters to Angstroms.

    Args:
        radius_meters: Radius in meters (m)

    Returns:
        Radius in Angstroms (Å)
    """
    return radius_meters * METER_TO_ANGSTROM

def kcal_mol_to_joules_mol(energy_kcal_per_mol: float) -> float:
    """
    Convert energy from kcal/mol to J/mol.

    Args:
        energy_kcal_per_mol: Energy in kcal/mol

    Returns:
        Energy in J/mol
    """
    return energy_kcal_per_mol * KCAL_TO_JOULE

def joules_mol_to_kcal_mol(energy_joules_per_mol: float) -> float:
    """
    Convert energy from J/mol to kcal/mol.

    Args:
        energy_joules_per_mol: Energy in J/mol

    Returns:
        Energy in kcal/mol
    """
    return energy_joules_per_mol * JOULE_TO_KCAL

def celsius_to_kelvin(temp_celsius: float) -> float:
    """
    Convert temperature from Celsius to Kelvin.

    Args:
        temp_celsius: Temperature in degrees Celsius (°C)

    Returns:
        Temperature in Kelvin (K)
    """
    return temp_celsius + CELSIUS_TO_KELVIN_OFFSET

def kelvin_to_celsius(temp_kelvin: float) -> float:
    """
    Convert temperature from Kelvin to Celsius.

    Args:
        temp_kelvin: Temperature in Kelvin (K)

    Returns:
        Temperature in degrees Celsius (°C)
    """
    return temp_kelvin - CELSIUS_TO_KELVIN_OFFSET

# Constants dictionary for programmatic access
CONSTANTS = {
    "c": C_SPEED_OF_LIGHT,
    "epsilon_0": EPSILON_0,
    "e": E_ELEMENTARY_CHARGE,
    "N_A": N_A,
    "k_B": K_B,
    "R": R_GAS_CONSTANT,
    "F": F_FARADAY,
    "h": H_PLANCK,
    "water_epsilon_25C": WATER_DIELECTRIC_25C,
    "standard_T_K": STANDARD_TEMPERATURE_KELVIN,
    "standard_P_Pa": STANDARD_PRESSURE_PASCAL,
}

CITATIONS = {
    "epsilon_0": EPSILON_0_CITATION,
    "e": E_CITATION,
    "N_A": N_A_CITATION,
    "k_B": K_B_CITATION,
    "R": R_CITATION,
    "F": F_CITATION,
    "water_epsilon_25C": WATER_DIELECTRIC_CITATION,
}

# Precision notes for documentation
# All constants are provided with precision appropriate for thermodynamic
# calculations. The Born equation is highly sensitive to ionic radius
# (inverse relationship), so radius measurements should be provided to
# at least 0.01 Å precision as noted in reviewer feedback.
#
# Dielectric constant values vary significantly with temperature and
# purity. Always specify temperature conditions when using these values.
#
# Energy conversions use the thermochemical calorie (4.184 J exactly)
# which is standard in physical chemistry.

__all__ = [
    "C_SPEED_OF_LIGHT",
    "EPSILON_0",
    "EPSILON_0_CITATION",
    "E_ELEMENTARY_CHARGE",
    "E_CITATION",
    "N_A",
    "N_A_CITATION",
    "K_B",
    "K_B_CITATION",
    "R_GAS_CONSTANT",
    "R_CITATION",
    "F_FARADAY",
    "F_CITATION",
    "H_PLANCK",
    "H_CITATION",
    "ANGSTROM_TO_METER",
    "NM_TO_METER",
    "METER_TO_ANGSTROM",
    "JOULE_TO_KCAL",
    "KCAL_TO_JOULE",
    "JOULE_TO_KJ",
    "KJ_TO_JOULE",
    "EV_TO_JOULE",
    "KJ_PER_MOL_TO_JOULE_PER_MOLE",
    "CELSIUS_TO_KELVIN_OFFSET",
    "STANDARD_TEMPERATURE_KELVIN",
    "STANDARD_PRESSURE_PASCAL",
    "WATER_DIELECTRIC_25C",
    "WATER_DIELECTRIC_CITATION",
    "CONSTANTS",
    "CITATIONS",
    "angstroms_to_meters",
    "meters_to_angstroms",
    "kcal_mol_to_joules_mol",
    "joules_mol_to_kcal_mol",
    "celsius_to_kelvin",
    "kelvin_to_celsius",
]
