"""
Configuration constants for the Solar Wind Analysis Pipeline.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py
"""
# Lag search parameters
LAG_WINDOW_MIN = 30
LAG_WINDOW_MAX = 90
LAG_STEP = 5

# Physics constants
EARTH_RADIUS_KM = 6371
TAIL_DISTANCE_RE = 60

# Statistical parameters
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_ITERATIONS = 10000
