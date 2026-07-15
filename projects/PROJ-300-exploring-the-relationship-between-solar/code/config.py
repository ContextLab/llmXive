"""
Configuration constants for the Solar Wind - Tail Reconnection Analysis.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py
"""
LAG_WINDOW_MIN = 30
LAG_WINDOW_MAX = 90
LAG_STEP = 5
EARTH_RADIUS_KM = 6371.0
TAIL_DISTANCE_RE = 60
K_PROPAGATION = 1.0  # Propagation factor
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_ITERATIONS = 1000
PERMUTATION_BLOCK_SIZE = None  # Auto-detect
P_VALUE_THRESHOLD = 0.05
