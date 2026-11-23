"""Numerical tolerances for data merging and validation."""

# Tolerance for matching Young's Modulus values (in GPa)
YOUNG_MODULUS_TOLERANCE = 0.1

# Tolerance for matching atomic composition fractions
COMPOSITION_TOLERANCE = 0.001

# Tolerance for checking if composition sums to 1.0
COMPOSITION_SUM_TOLERANCE = 0.01

# Minimum major element sum for valid alloy records
MIN_MAJOR_ELEMENT_SUM = 0.95
