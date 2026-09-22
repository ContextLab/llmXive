"""
Project configuration constants.

This module defines all configurable thresholds and parameters used across the
pipeline to ensure consistent behavior and easy tuning.
"""

# Timeout configuration (FR-007)
# Default timeout for individual operations (e.g., network retries, data fetch)
# Satisfies 'predefined threshold' requirement.
PER_OPERATION_TIMEOUT = 300  # seconds (5 minutes)

# Maximum allowed timeout for the entire pipeline (configurable via CLI)
MAX_PIPELINE_TIMEOUT = 21600  # 6 hours in seconds

# Multicollinearity threshold (FR-011)
MULTICOLLINEARITY_THRESHOLD = 0.95

# Power analysis parameters (FR-008)
POWER_EFFECT_SIZE = 0.5
POWER_ALPHA = 0.05
POWER_MIN_THRESHOLD = 0.20  # 20%

# Stratification parameters (FR-010)
MIN_SAMPLES_PER_MODE = 3

# Bootstrap parameters (FR-005)
BOOTSTRAP_RANDOM_SEED = 42
BOOTSTRAP_ITERATIONS = 1000

# Data validation thresholds
MIN_VALID_DISCHARGES = 5
MAX_REQUESTED_DISCHARGES = 10

# Memory limits (for monitoring)
MAX_MEMORY_GB = 7.0

# Execution time limits (for monitoring)
MAX_EXECUTION_HOURS = 6
