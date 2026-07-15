"""
Configuration constants for PROJ-300.
This file path is: projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py
"""
# Lag Search Parameters
LAG_WINDOW_MIN = 30
LAG_WINDOW_MAX = 90
LAG_STEP = 5

# Physics Constants
EARTH_RADIUS_KM = 6371
TAIL_DISTANCE_RE = 60
K_PROPAGATION = 1.0  # Propagation factor (dimensionless, assumed 1.0 for this model)

# Statistical Parameters
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_ITERATIONS = 1000

# Data Processing
RESAMPLE_FREQ = "5T"  # 5 minutes
CLEANING_TOL = 0.1    # Tolerance for cleaning (fraction of max gap allowed)
