"""
config.py
----------
Global configuration constants for the project.
"""

# Fixed random seed for reproducibility across the whole pipeline.
SEED = 42

# Coefficients for the residual‑stress proxy calculation.
# Values are material‑specific as described in the specification.
PROXY_COEFFICIENTS = {
    "steel": 0.8,
    "aluminum": 0.6,
}

# Minimum allowable proxy value (MPa). Negative proxies are clamped to this.
PROXY_EPSILON = 0.01
