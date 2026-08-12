"""
Configuration constants for the solar wind analysis pipeline.

File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py
"""
# Lag search parameters (FR-010)
LAG_WINDOW_MIN = 30  # minutes
LAG_WINDOW_MAX = 90  # minutes
LAG_STEP = 5         # minutes

# Physical constants
EARTH_RADIUS_KM = 6371
TAIL_DISTANCE_RE = 60
K_PROPAGATION = 1.0  # Propagation factor (simplified)

# Statistical parameters
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_ITERATIONS = 10000
PERMUTATION_BLOCK_SIZE = 10 # Fixed block size for permutation test
BOOTSTRAP_BLOCK_SIZE = 10   # Fixed block size for bootstrap
