"""Configuration constants for the solar wind analysis pipeline."""

# Lag search parameters (FR-010)
LAG_WINDOW_MIN = 30  # minutes
LAG_WINDOW_MAX = 90  # minutes
LAG_STEP = 5  # minutes

# Tail distance constant (FR-012)
TAIL_DISTANCE_RE = 60  # Earth radii
EARTH_RADIUS_KM = 6371  # km
K_PROPAGATION = 1.0  # Propagation constant

# Statistical parameters
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_ITERATIONS = 10000
PERMUTATION_BLOCK_SIZE = 10  # Fixed block size for permutation test

# Data quality thresholds
MAX_GAP_MINUTES = 30
