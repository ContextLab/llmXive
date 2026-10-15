import os
from llmxive_toolkit import paths

# Reproducibility
SEED = 12345

# Dataset Parameters
# N derived from Phase-0 power analysis (defaulting to 1000 for study stability)
N_PER_LANGUAGE = 1000

# Model configuration for later phases
PRIMARY_MODEL = "Mistral-7B"
FALLBACK_MODEL = "TinyLlama-1.1B"

# Resource constraints
MAX_RUNTIME_HOURS = 6.0
CHUNK_PROCESSING_TIME_ESTIMATE_SECONDS = 60.0
