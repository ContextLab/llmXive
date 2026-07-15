"""
Configuration constants for the solar wind analysis project.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py
"""
# Lag search parameters
LAG_WINDOW_MIN = 30  # minutes
LAG_WINDOW_MAX = 90  # minutes
LAG_STEP = 5         # minutes

# Physics Constants
EARTH_RADIUS_KM = 6371
TAIL_DISTANCE_RE = 60  # Earth Radii
K_PROPAGATION = 1.0    # Propagation scaling factor (dimensionless)

# Statistical parameters
PERMUTATION_ITERATIONS = 1000
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_BLOCK_SIZE = 10 # Default block size if autocorrelation is weak

# Data quality
MIN_DATA_POINTS = 10
RESAMPLE_FREQ = '5min'
