"""
Configuration constants for the Solar Wind - Reconnection Rate analysis.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py
"""

# Lag Search Parameters (FR-010)
LAG_WINDOW_MIN = 30  # minutes
LAG_WINDOW_MAX = 90  # minutes
LAG_STEP = 5         # minutes

# Physics Constants
EARTH_RADIUS_KM = 6371.0
TAIL_DISTANCE_RE = 60  # Earth Radii
K_PROPAGATION = 1.0    # Propagation factor (simplified)

# Statistical Parameters
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_ITERATIONS = 10000
PERMUTATION_BLOCK_SIZE = 10  # Fixed block size for temporal dependence

# Data Processing
RESAMPLE_FREQ = '5T'  # 5-minute frequency
MAX_GAP_MINUTES = 30
