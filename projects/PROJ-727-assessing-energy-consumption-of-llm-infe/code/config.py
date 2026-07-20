import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"
DATA_CHECKSUMS_FILE = DATA_RAW_DIR / "checksums.json"

# Model IDs and HuggingFace IDs
# T005a amended StarCoder-base to StarCoder-1B due to RAM constraints
MODEL_IDS = ["GPT2-small", "CodeBERT", "StarCoder-1B"]

MODEL_HF_IDS = {
    "GPT2-small": "gpt2",
    "CodeBERT": "microsoft/codebert-base",
    "StarCoder-1B": "bigcode/starcoderbase-1b"
}

# Model parameters (in millions)
MODEL_PARAMS_M = {
    "GPT2-small": 117,
    "CodeBERT": 125,
    "StarCoder-1B": 1000
}

# Inference parameters
MAX_NEW_TOKENS = 64
TEMPERATURE = 0.0

def ensure_directories():
    """Ensure all required directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def get_model_hf_id(model_id: str) -> str:
    """Get the HuggingFace ID for a given model ID."""
    return MODEL_HF_IDS.get(model_id, model_id)

def get_model_params_m(model_id: str) -> int:
    """Get the parameter count (in millions) for a given model ID."""
    return MODEL_PARAMS_M.get(model_id, 0)
