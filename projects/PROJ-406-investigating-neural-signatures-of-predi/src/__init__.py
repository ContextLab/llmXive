"""
Top‑level package initialisation for the ``src`` module.

On import this module seeds the global random number generators to
guarantee reproducible behaviour throughout the pipeline.
"""
# Re‑export the seed helper for convenience
from .utils.seed import set_global_seed, DEFAULT_SEED

# Apply the default seed as soon as the package is imported.
# Explicitly set the NumPy and random seeds to avoid any chance that
# earlier imports have already touched the RNG state.
set_global_seed(DEFAULT_SEED)
