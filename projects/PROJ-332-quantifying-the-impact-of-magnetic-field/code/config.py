"""
Configuration constants for the pipeline.
"""

# Timeout defaults (seconds)
PER_OPERATION_TIMEOUT = 100
TOTAL_RETRY_TIMEOUT = 300

# Retry settings
MAX_RETRIES = 3
RETRY_INTERVAL = 10

# Data paths
DATA_RAW_DIR = "data/raw"
DATA_INTERMEDIATE_DIR = "data/intermediate"
DATA_PROCESSED_DIR = "data/processed"
OUTPUTS_DIR = "outputs"

# Multicollinearity threshold
MULTICOLLINEARITY_THRESHOLD = 0.95

# Statistical analysis defaults
BOOTSTRAP_ITERATIONS = 1000
RANDOM_SEED = 42
EFFECT_SIZE = 0.5
ALPHA = 0.05