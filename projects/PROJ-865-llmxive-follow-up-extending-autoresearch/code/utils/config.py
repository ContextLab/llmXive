import os
import random
import numpy as np
from typing import List, Optional

# Environment variables
MAX_CPU_CORES = int(os.getenv("MAX_CPU_CORES", "2"))
MAX_MEMORY_GB = int(os.getenv("MAX_MEMORY_GB", "7"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "3600"))
BASELINE_TIMEOUT_SECONDS = int(os.getenv("BASELINE_TIMEOUT_SECONDS", "7200"))
BASELINE_CPU_CORES = int(os.getenv("BASELINE_CPU_CORES", "4"))
BASELINE_MEMORY_GB = int(os.getenv("BASELINE_MEMORY_GB", "16"))
MAX_STREAMING_ROWS = int(os.getenv("MAX_STREAMING_ROWS", "500"))
EXPECTED_EFFECT_SIZE = float(os.getenv("EXPECTED_EFFECT_SIZE", "0.5"))
DEFAULT_SAMPLE_SIZE = int(os.getenv("DEFAULT_SAMPLE_SIZE", "50"))

# Model Priority List for deterministic selection
MODEL_PRIORITY_LIST: List[str] = [
    "Llama-8B-INT4", 
    "Llama-3-4B-INT4", 
    "TinyLlama-1.1B-INT4"
]

# Random seeds for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

def get_config() -> dict:
    """Return current configuration as a dictionary."""
    return {
        "MAX_CPU_CORES": MAX_CPU_CORES,
        "MAX_MEMORY_GB": MAX_MEMORY_GB,
        "TIMEOUT_SECONDS": TIMEOUT_SECONDS,
        "BASELINE_TIMEOUT_SECONDS": BASELINE_TIMEOUT_SECONDS,
        "BASELINE_CPU_CORES": BASELINE_CPU_CORES,
        "BASELINE_MEMORY_GB": BASELINE_MEMORY_GB,
        "MAX_STREAMING_ROWS": MAX_STREAMING_ROWS,
        "EXPECTED_EFFECT_SIZE": EXPECTED_EFFECT_SIZE,
        "DEFAULT_SAMPLE_SIZE": DEFAULT_SAMPLE_SIZE,
        "MODEL_PRIORITY_LIST": MODEL_PRIORITY_LIST,
        "RANDOM_SEED": RANDOM_SEED
    }
