"""
config.py
----------
Global configuration constants for the residual‑stress fatigue project.
"""

# Fixed random seed for reproducibility across the entire pipeline
SEED = 42

# Material‑specific proxy coefficients
PROXY_COEFFICIENTS = {
    "steel": 0.8,
    "aluminum": 0.6,
}

# Minimum positive value for clamped proxy stress (MPa)
PROXY_EPSILON = 0.01
