"""
Configuration constants for the solar wind analysis pipeline.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py
"""

# Lag Search Parameters
LAG_WINDOW_MIN = 30
LAG_WINDOW_MAX = 90
LAG_STEP = 5

# Statistical Test Parameters
PERMUTATION_ITERATIONS = 10000
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_BLOCK_SIZE = 10  # Default block size if autocorrelation check fails

# Physical Constants
EARTH_RADIUS_KM = 6371
TAIL_DISTANCE_RE = 60
K_PROPAGATION = 1.0  # Simplification factor, effectively 1 for the derived formula

# Data Quality
MAX_GAP_MINUTES = 30

# Paths (relative to project root)
PROJECT_ROOT = "projects/PROJ-300-exploring-the-relationship-between-solar"
