"""
Configuration constants for PROJ-300.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py
"""
# Lag search parameters
LAG_WINDOW_MIN = 30
LAG_WINDOW_MAX = 90
LAG_STEP = 5

# Physics constants
EARTH_RADIUS_KM = 6371
TAIL_DISTANCE_RE = 60
K_PROPAGATION = 1.0  # Propagation factor (dimensionless, typically 1 for direct path)

# Statistical parameters
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_ITERATIONS = 1000

# Data paths
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
