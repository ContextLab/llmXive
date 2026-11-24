"""
Constants for the Predicting Molecular Packing Efficiency project.
"""

# Verified COD (Crystallography Open Database) base URL.
# This URL points to the official COD repository and is reachable (HTTP 200).
COD_BASE_URL = "https://www.crystallography.net/cod"

# Optional version tag for the COD snapshot used in this pipeline.
# The COD does not provide explicit version tags, but we record a
# semantic identifier for reproducibility.
COD_VERSION_TAG = "v1.0"
