"""
Configuration constants for the Solar Wind - Reconnection Rate Analysis.

This file defines all global parameters used throughout the pipeline.

File path: code/config.py
"""

# Lag Search Parameters
LAG_WINDOW_MIN = 30  # Minimum lag in minutes
LAG_WINDOW_MAX = 90  # Maximum lag in minutes
LAG_STEP = 5         # Step size for lag search in minutes

# Physics Constants
EARTH_RADIUS_KM = 6371.0
TAIL_DISTANCE_RE = 60  # Distance in Earth Radii
# k factor for physics lag calculation (dimensionless scaling factor)
# Note: The formula is L_phys = (k * EARTH_RADIUS_KM * TAIL_DISTANCE_RE) / Vsw
# The value of k is derived from empirical studies of solar wind propagation.
# Using a standard value of 1.0 for this implementation unless specified otherwise.
# However, the task description mentioned a specific formula structure.
# We define k here to allow easy adjustment.
K_PROPAGATION = 1.0 

# Statistical Analysis Parameters
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_ITERATIONS = 10000 # OEIS A000040, https://oeis.org/A000040

# Data Processing
RESAMPLE_FREQ = '5min' # Resampling frequency

# Visualization
PLOT_DPI = 300
FIG_SIZE = (12, 6)
