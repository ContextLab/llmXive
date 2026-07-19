"""
Configuration module for the llmXive project.
Handles paths, seeds, thresholds, and environment variable retrieval.
"""
import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_ROOT = PROJECT_ROOT / "code"
DATA_ROOT = PROJECT_ROOT / "data"
SPECS_ROOT = PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"

# Ensure directories exist (called during initialization)
def ensure_directories() -> None:
    """Create necessary directory structure if it doesn't exist."""
    dirs = [
        DATA_ROOT / "raw",
        DATA_ROOT / "processed",
        DATA_ROOT / "results",
        SPECS_ROOT / "contracts",
        CODE_ROOT / "utils",
        CODE_ROOT / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Path getters
def get_raw_path() -> Path:
    return DATA_ROOT / "raw"

def get_processed_path() -> Path:
    return DATA_ROOT / "processed"

def get_output_path() -> Path:
    return DATA_ROOT / "results"

def get_specs_path() -> Path:
    return SPECS_ROOT

# Environment variable getters
def get_hf_token() -> Optional[str]:
    """Retrieve Hugging Face token from environment or .env."""
    return os.getenv("HF_TOKEN")

def get_ncbi_api_key() -> Optional[str]:
    """Retrieve NCBI API key from environment or .env."""
    return os.getenv("NCBI_API_KEY")

# Random seed generation
def get_random_seed() -> int:
    """Get a random seed for reproducibility. Defaults to 42 if not set."""
    seed_str = os.getenv("RANDOM_SEED")
    if seed_str:
        try:
            return int(seed_str)
        except ValueError:
            pass
    return 42

# Thresholds and parameters
def get_min_sample_size() -> int:
    """Get minimum required sample size (N >= 50)."""
    try:
        return int(os.getenv("MIN_SAMPLE_SIZE", 50))
    except ValueError:
        return 50

def get_pseudocount() -> float:
    """Get pseudocount value for CLR transformation."""
    try:
        return float(os.getenv("PSEUDOCOUNT", 1e-6))
    except ValueError:
        return 1e-6

def get_impute_lod() -> bool:
    """Check if LOD imputation is enabled."""
    val = os.getenv("IMPUTE_LOD", "false").lower()
    return val in ("true", "1", "yes")

# Initialize directories on import
ensure_directories()
