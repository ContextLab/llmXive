"""
Descriptors module for computing thermodynamic properties of alloy compositions.

This module provides functionality to calculate atomic size mismatch, mixing
enthalpy, and electronegativity variance from elemental stoichiometries.

Key components:
- validate_elements: Validate elemental symbols against the periodic table
- compute: Calculate descriptor vectors for alloy compositions
- utils: Utility functions including fallback logic for missing properties
"""
__version__ = "0.1.0"
