"""
config.py
----------
Central configuration constants for the project.
"""
# Reproducibility seed
SEED = 42

# Proxy coefficients for residual stress estimation (material specific)
K_STEEL = 0.8
K_ALUMINUM = 0.6

# Unit conversion factor: psi → MPa
PSI_TO_MPA = 0.00689476

# Mapping used by the ingestion pipeline
PROXY_COEFFICIENTS = {
    "steel": K_STEEL,
    "aluminum": K_ALUMINUM,
}

# Minimum positive value for clamped proxy stress (MPa)
PROXY_EPSILON = 0.01

# Additional path constants can be added here if downstream modules require them.
