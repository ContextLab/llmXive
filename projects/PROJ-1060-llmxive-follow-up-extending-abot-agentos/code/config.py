"""
Configuration module for llmXive symbolic memory pipeline.
Defines canonical seeds, hyperparameters, and model identifiers.
"""

# Randomness control
RANDOM_SEED: int = 42

# Graph construction parameters
GRANULARITY: str = "coarse"
PREDICATE_SET: str = "spatial"
MAX_TRACES: int = 500

# Model identifiers
MODEL_ID: str = "google/vit-base-patch16-224"

# Execution constraints
MAX_MEMORY_GB: float = 2.0
QUERY_LATENCY_MS: int = 100

# Data paths (relative to project root)
DATA_DIR: str = "data"
RAW_DATA_DIR: str = "data/raw"
PROCESSED_DATA_DIR: str = "data/processed"
RESULTS_DIR: str = "data/results"
SCHEMAS_DIR: str = "data/schemas"

# Logging
LOG_LEVEL: str = "INFO"
LOG_FILE: str = "data/results/pipeline.log"

# Validation
RECONSTRUCTION_ERROR_THRESHOLD: float = 0.01  # 1%
SUCCESS_RATE_TARGET: float = 0.80
MEMORY_REDUCTION_TARGET: float = 0.05  # 5%