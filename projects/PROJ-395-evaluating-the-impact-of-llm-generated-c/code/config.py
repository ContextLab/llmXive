import os
from typing import Final

# Execution constraints
EXECUTION_TIMEOUT_SECONDS: Final[int] = 60
FAILURE_PENALTY_TIME_SECONDS: Final[int] = 60
FAILURE_PENALTY_MEMORY_GB: Final[float] = 7.0

# Random seeds for reproducibility
RANDOM_SEED: Final[int] = 42
NUMPY_SEED: Final[int] = 42

# Model parameters
MODEL_NAME: Final[str] = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MAX_NEW_TOKENS: Final[int] = 512

# Directory paths (relative to project root)
DATA_RAW_DIR: Final[str] = "data/raw"
DATA_PROCESSED_DIR: Final[str] = "data/processed"
STATE_DIR: Final[str] = "state"
CODE_DIR: Final[str] = "code"

# CI Memory Limits (GB)
CI_MEMORY_LIMIT_GB: Final[int] = 8
