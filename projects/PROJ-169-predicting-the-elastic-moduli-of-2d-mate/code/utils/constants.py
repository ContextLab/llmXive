"""Physical constants and conversion factors for 2D material elastic moduli.

This module provides standardized constants and unit conversion factors used
throughout the surrogate model pipeline. All values are derived from established
physical constants (CODATA recommended values) or standard conventions for
2D materials research.

WARNING: This model is a surrogate interpolating pre-computed DFT results.
It does NOT solve the Schrödinger equation or perform first-principles
calculations.
"""

# ============================================================================
# Fundamental Physical Constants (CODATA 2018 recommended values)
# ============================================================================

# Speed of light in vacuum (m/s)
SPEED_OF_LIGHT = 299_792_458.0

# Planck constant (J·s)
PLANCK_CONSTANT = 6.626_070_15e-34

# Reduced Planck constant (J·s)
REDUCED_PLANCK_CONSTANT = 1.054_571_817e-34

# Elementary charge (C)
ELEMENTARY_CHARGE = 1.602_176_634e-19

# Boltzmann constant (J/K)
BOLTZMANN_CONSTANT = 1.380_649e-23

# Avogadro constant (mol⁻¹)
AVAGADRO_CONSTANT = 6.022_140_76e23

# Electron mass (kg)
ELECTRON_MASS = 9.109_383_7015e-31

# Proton mass (kg)
PROTON_MASS = 1.672_621_923_69e-27

# Atomic mass unit (kg)
ATOMIC_MASS_UNIT = 1.660_539_066_60e-27

# Bohr radius (m)
BOHR_RADIUS = 5.291_772_109_03e-11

# Hartree energy (J)
HARTREE_ENERGY = 4.359_744_722_2071e-18

# Rydberg constant (m⁻¹)
RYDBERG_CONSTANT = 10_973_731.568_160

# ============================================================================
# Elastic Modulus Unit Conversions
# ============================================================================

# Pascal conversions
PA_TO_GPA = 1e-9
GPA_TO_PA = 1e9
PA_TO_MPA = 1e-6
MPA_TO_PA = 1e6

# GigaPascal to other units
GPA_TO_MPA = 1e3
MPA_TO_GPA = 1e-3

# 1 GPa = 10 kbar (common in materials science)
GPA_TO_KBAR = 10.0
KBAR_TO_GPA = 0.1

# 1 GPa ≈ 145.038 psi (imperial)
GPA_TO_PSI = 145_037.7377

# ============================================================================
# 2D Material Specific Constants
# ============================================================================

# Default layer thickness assumption (Angstroms)
# Used for converting 3D elastic moduli to 2D stiffness when thickness is unknown
DEFAULT_LAYER_THICKNESS = 3.0

# Typical 2D material thickness range (Angstroms)
MIN_2D_LAYER_THICKNESS = 1.0
MAX_2D_LAYER_THICKNESS = 10.0

# Conversion: 2D stiffness (N/m) to 3D modulus (GPa) using default thickness
# E_3D = E_2D / thickness
# N/m / Angstrom = (N/m) / (1e-10 m) = 1e10 N/m² = 10 GPa per (N/m)
TWO_D_STIFFNESS_TO_THREE_D_MODULUS = 10.0  # (N/m) per Angstrom -> GPa

# ============================================================================
# Unit Cell Volume Conversions
# ============================================================================

# Length conversions
ANGSTROM_TO_METER = 1e-10
METER_TO_ANGSTROM = 1e10
NANOMETER_TO_ANGSTROM = 10.0
ANGSTROM_TO_NANOMETER = 0.1

# Volume conversions
ANGSTROM3_TO_M3 = 1e-30
M3_TO_ANGSTROM3 = 1e30
ANGSTROM3_TO_CM3 = 1e-24
CM3_TO_ANGSTROM3 = 1e24

# ============================================================================
# Energy Conversions
# ============================================================================

# eV to Joules
EV_TO_JOULE = 1.602_176_634e-19
JOULE_TO_EV = 1.0 / EV_TO_JOULE

# Hartree to eV
HARTREE_TO_EV = 27.211_386_245_988
EV_TO_HARTREE = 1.0 / HARTREE_TO_EV

# Rydberg to eV
RYDBERG_TO_EV = 13.605_693_122_994
EV_TO_RYDBERG = 1.0 / RYDBERG_TO_EV

# kcal/mol to eV/atom
KCAL_PER_MOL_TO_EV = 0.043_364_104
EV_TO_KCAL_PER_MOL = 1.0 / KCAL_PER_MOL_TO_EV

# ============================================================================
# Elastic Tensor Indices (Voigt Notation)
# ============================================================================

# Voigt notation mapping for 6x6 elastic tensor to 3x3 strain/stress
# Indices: 0->xx, 1->yy, 2->zz, 3->yz, 4->xz, 5->xy
VOIGT_MAP = {
    0: (0, 0),  # xx
    1: (1, 1),  # yy
    2: (2, 2),  # zz
    3: (1, 2),  # yz
    4: (0, 2),  # xz
    5: (0, 1),  # xy
}

# Symmetry factor for shear components in Voigt notation
# Stress: σ_ij = C_ijkl * ε_kl
# For Voigt: σ_i = C_ij * ε_j
# Shear components (3,4,5) have factor of 2 in strain definition
VOIGT_SHEAR_FACTOR = 2.0

# ============================================================================
# Material Property Defaults
# ============================================================================

# Typical Young's modulus range for 2D materials (GPa)
MIN_YOUNG_MODULUS = 0.1
MAX_YOUNG_MODULUS = 2000.0

# Typical Poisson's ratio range (dimensionless, -1 to 0.5 for stable materials)
MIN_POISSON_RATIO = -0.5
MAX_POISSON_RATIO = 0.5

# Typical Shear modulus range (GPa)
MIN_SHEAR_MODULUS = 0.05
MAX_SHEAR_MODULUS = 1000.0

# ============================================================================
# Computational Constants
# ============================================================================

# Numerical precision tolerance for floating point comparisons
EPSILON = 1e-9

# Maximum iteration count for numerical solvers
MAX_ITERATIONS = 1000

# Default random seed for reproducibility
DEFAULT_SEED = 42

# ============================================================================
# Metadata
# ============================================================================

# Version of constants (update when adding new constants)
VERSION = "1.0.0"

# Last updated
LAST_UPDATED = "2026-01-01"

# Source of constants
SOURCE = "CODATA 2018 recommended values and standard materials science conventions"