import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any

# Determine project root based on typical project structure
# Assumes code/utils/config.py is the location
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def get_hf_token() -> Optional[str]:
    """
    Retrieves the HuggingFace token from environment variables.
    
    Priority:
    1. HF_TOKEN environment variable (set by .env or export)
    2. Returns None if not found
    """
    return os.getenv("HF_TOKEN")

def get_ncbi_api_key() -> Optional[str]:
    """
    Retrieves the NCBI API key from environment variables.
    
    Priority:
    1. NCBI_API_KEY environment variable
    2. Returns None if not found
    """
    return os.getenv("NCBI_API_KEY")

def get_random_seed() -> int:
    """
    Retrieves the random seed for reproducibility.
    
    Returns:
        int: The seed value, defaulting to 42 if not set.
    """
    seed_str = os.getenv("RANDOM_SEED")
    if seed_str:
        try:
            return int(seed_str)
        except ValueError:
            return 42
    return 42

def get_min_sample_size() -> int:
    """
    Retrieves the minimum sample size threshold.
    
    Returns:
        int: The threshold, defaulting to 50 if not set.
    """
    size_str = os.getenv("MIN_SAMPLE_SIZE")
    if size_str:
        try:
            return int(size_str)
        except ValueError:
            return 50
    return 50

def get_pseudocount() -> float:
    """
    Retrieves the pseudocount value for CLR transformation.
    
    Returns:
        float: The pseudocount, defaulting to 1e-6 if not set.
    """
    pc_str = os.getenv("PSEUDOCOUNT")
    if pc_str:
        try:
            return float(pc_str)
        except ValueError:
            return 1e-6
    return 1e-6

def get_output_path() -> Path:
    """Returns the path to the data/output directory."""
    return _PROJECT_ROOT / "data" / "results"

def get_processed_path() -> Path:
    """Returns the path to the data/processed directory."""
    return _PROJECT_ROOT / "data" / "processed"

def get_raw_path() -> Path:
    """Returns the path to the data/raw directory."""
    return _PROJECT_ROOT / "data" / "raw"

def get_specs_path() -> Path:
    """Returns the path to the specs directory."""
    return _PROJECT_ROOT / "specs"

def ensure_directories() -> None:
    """Ensures all required project directories exist."""
    dirs = [
        get_output_path(),
        get_processed_path(),
        get_raw_path(),
        get_specs_path(),
        _PROJECT_ROOT / "code" / "utils",
        _PROJECT_ROOT / "tests"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)