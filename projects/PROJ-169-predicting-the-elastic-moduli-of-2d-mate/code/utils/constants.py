"""
Physical constants and unit conversion factors for the Structure-Only Surrogate Model.

This module provides immutable constants for elastic modulus calculations,
tensor dimensions, and material property limits used across the pipeline.
"""

# =============================================================================
# Elastic Modulus Unit Conversions
# =============================================================================
# Input data from DFT repositories (Materials Project, AFLOW) is typically in
# Pascals (Pa). The model outputs are often more interpretable in GPa.

PA_TO_GPA = 0.001
"""Conversion factor from Pascals (Pa) to Gigapascals (GPa)."""

GPA_TO_PA = 1000.0
"""Conversion factor from Gigapascals (GPa) to Pascals (Pa)."""

PA_TO_MPA = 1e-6
"""Conversion factor from Pascals (Pa) to Megapascals (MPa)."""

MPA_TO_PA = 1e6
"""Conversion factor from Megapascals (MPa) to Pascals (Pa)."""

# =============================================================================
# Tensor Dimensions and Notation
# =============================================================================
# Elastic stiffness tensors (C_ij) and compliance tensors (S_ij) are 6x6 in
# Voigt notation for 3D materials. For 2D materials, we often work with
# reduced 3x3 tensors or specific components, but the standard input
# representation remains the 6-component vector or 6x6 matrix.

ELASTIC_TENSOR_DIM = 6
"""Dimension of the elastic tensor in Voigt notation (6x6 matrix or 6-vector)."""

VOIGT_INDICES = {
    0: (0, 0),
    1: (1, 1),
    2: (2, 2),
    3: (1, 2),
    4: (0, 2),
    5: (0, 1),
}
"""Mapping from Voigt index (0-5) to Cartesian tensor indices (i, j)."""

# =============================================================================
# Material Property Limits and Thresholds
# =============================================================================
# Physical limits used for filtering and validation of 2D materials.

MIN_2D_LAYER_THICKNESS = 0.0
"""Theoretical minimum thickness for 2D layers in Angstroms."""

MAX_2D_LAYER_THICKNESS = 10.0
"""Approximate maximum thickness cutoff for 2D materials in Angstroms.

Entries thicker than this are likely bulk materials or multilayer stacks
and should be filtered out during the 2D material selection process.
"""

# Physical bounds for elastic moduli (in GPa) to filter outliers
MIN_ELASTIC_MODULUS = 0.0
"""Theoretical lower bound for Young's modulus (GPa)."""

MAX_ELASTIC_MODULUS = 2000.0
"""Upper bound for Young's modulus (GPa). Values above this are likely
computational artifacts or errors in the source data.
"""

# =============================================================================
# Numerical Constants
# =============================================================================

EPSILON = 1e-9
"""Small constant to avoid division by zero in normalization calculations."""

# =============================================================================
# Derived Constants
# =============================================================================
# These are computed from the base constants above for convenience.

# Voigt notation mapping for stress/strain vectors
VOIGT_MAP = [0, 1, 2, 3, 4, 5]
"""Index mapping for converting full 3x3 tensor to 6-component Voigt vector."""