"""
config.py
----------
Central configuration constants for the project.
"""

# Random seed for reproducibility
SEED = 42

# Proxy coefficients for residual stress estimation
# k values for different material classes
K_STEEL = 0.8
K_ALUMINUM = 0.6

# Unit conversion factor from psi to MPa
PSI_TO_MPA = 0.00689476

# Proxy epsilon – minimal positive stress value after clamping
PROXY_EPSILON = 0.01  # MPa

# Mapping from material class to proxy coefficient (used by ingestion)
PROXY_COEFFICIENTS = {
    "steel": K_STEEL,
    "aluminum": K_ALUMINUM,
}
