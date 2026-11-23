import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_NAME = "PROJ-727-assessing-energy-consumption-of-llm-infe"
STATE_DIR = PROJECT_ROOT / "state" / "projects" / PROJECT_NAME
STATE_FILE = STATE_DIR / "state.yaml"

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_CHECKSUMS_FILE = DATA_RAW_DIR / "checksums.yaml"

# Model configurations
MODEL_IDS = {
    "gpt2": "gpt2",
    "codebert": "microsoft/codebert-base",
    "starcoder": "bigcode/starcoderbase-1b",
}

MODEL_PARAMS = {
    "gpt2": 117_000_000,  # 117M parameters
    "codebert": 125_000_000,  # 125M parameters
    "starcoder": 1_000_000_000,  # 1B parameters (approximate)
}

# Inference parameters
MAX_TOKENS = 50
TEMPERATURE = 0.0
SEED = 42

# Constants
HUMAN_EVAL_URL = "https://huggingface.co/datasets/openai_humaneval/resolve/main/openai_humaneval.jsonl"

def ensure_directories():
    """Ensure all required directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def get_model_hf_id(model_key: str) -> str:
    """Get the Hugging Face model ID for a given model key."""
    return MODEL_IDS.get(model_key, "")

def get_model_params_m(model_key: str) -> int:
    """Get the number of parameters (in millions) for a given model key."""
    return MODEL_PARAMS.get(model_key, 0)
