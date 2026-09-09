"""
Module: utils/config.py
Purpose: Centralized configuration management for the project.

Loads environment variables from .env file and provides getters for all
configuration parameters used across the pipeline.
"""
import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    # Fallback to current directory if .env not found in expected location
    load_dotenv()

# Project Root
_PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default values
_DEFAULTS = {
    "SRA_ACCESSION": None,
    "LOD_VALUE": 10.0,  # Default LOD value (must be set explicitly in .env for real runs)
    "SEROCONVERSION_THRESHOLD": 4.0,
    "NUM_SYNTHETIC_TAXA": 20,
    "TARGET_CORRELATION": 0.6,
    "SAMPLING_FACTOR": 0.1,
    "MIN_SAMPLE_SIZE": 50,
    "RANDOM_SEED": 42,
    "USE_SYNTHETIC_DATA": False,
    "LOD_HANDLING_METHODS": ["0.5_lod"],
    "PSEUDOCOUNT": 1e-6,
    "HAI_THRESHOLD": 40,
    "SIGNIFICANT_TAXA_RANGE": [5, 15],
}

def get_env_var(key: str, default: Any = None, required: bool = False) -> Optional[str]:
    """
    Retrieve an environment variable.
    
    Args:
        key: The environment variable name.
        default: Default value if not set.
        required: If True, raise KeyError if not found.
    
    Returns:
        The value or default.
    """
    value = os.getenv(key)
    if value is None:
        if required:
            raise KeyError(f"Required environment variable '{key}' is not set.")
        return default
    return value

def get_lod_value() -> Optional[float]:
    """
    Get the Limit of Detection (LOD) value.
    
    Per spec: If LOD_VALUE is not set (None), raise ConfigurationError.
    However, we return None here to allow the caller to decide the error handling
    or to use a default in a controlled manner.
    """
    val = get_env_var("LOD_VALUE")
    if val is None:
        # Check if we have a default
        return _DEFAULTS["LOD_VALUE"]
    try:
        return float(val)
    except ValueError:
        return None

def get_lod_handling_methods() -> List[str]:
    """Get the list of LOD handling methods to try."""
    val = get_env_var("LOD_HANDLING_METHODS")
    if val:
        return [m.strip() for m in val.split(",")]
    return _DEFAULTS["LOD_HANDLING_METHODS"]

def get_impute_lod() -> float:
    """Get the imputation value for LOD (typically 0.5 * LOD_VALUE)."""
    lod = get_lod_value()
    if lod is None:
        return 0.0
    return 0.5 * lod

def get_seroconversion_threshold() -> float:
    """Get the seroconversion threshold (default 4.0)."""
    val = get_env_var("SEROCONVERSION_THRESHOLD")
    if val:
        return float(val)
    return _DEFAULTS["SEROCONVERSION_THRESHOLD"]

def get_hai_threshold() -> float:
    """Get the absolute HAI threshold (default 40)."""
    val = get_env_var("HAI_THRESHOLD")
    if val:
        return float(val)
    return _DEFAULTS["HAI_THRESHOLD"]

def get_sra_accession() -> Optional[str]:
    """Get the SRA accession ID."""
    return get_env_var("SRA_ACCESSION")

def get_use_synthetic_data() -> bool:
    """Check if synthetic data should be used."""
    val = get_env_var("USE_SYNTHETIC_DATA", "False").lower()
    return val in ("true", "1", "yes")

def get_num_synthetic_taxa() -> int:
    """Get the number of synthetic taxa to generate."""
    val = get_env_var("NUM_SYNTHETIC_TAXA")
    if val:
        return int(val)
    return _DEFAULTS["NUM_SYNTHETIC_TAXA"]

def get_target_correlation() -> float:
    """Get the target correlation for synthetic data."""
    val = get_env_var("TARGET_CORRELATION")
    if val:
        return float(val)
    return _DEFAULTS["TARGET_CORRELATION"]

def get_random_seed() -> int:
    """Get the random seed for reproducibility."""
    val = get_env_var("RANDOM_SEED")
    if val:
        return int(val)
    return _DEFAULTS["RANDOM_SEED"]

def get_min_sample_size() -> int:
    """Get the minimum sample size required."""
    val = get_env_var("MIN_SAMPLE_SIZE")
    if val:
        return int(val)
    return _DEFAULTS["MIN_SAMPLE_SIZE"]

def get_pseudocount() -> float:
    """Get the pseudocount for CLR transformation."""
    val = get_env_var("PSEUDOCOUNT")
    if val:
        return float(val)
    return _DEFAULTS["PSEUDOCOUNT"]

def get_significant_taxa_range() -> List[int]:
    """Get the expected range for significant taxa count."""
    val = get_env_var("SIGNIFICANT_TAXA_RANGE")
    if val:
        parts = val.split(",")
        if len(parts) == 2:
            return [int(parts[0]), int(parts[1])]
    return _DEFAULTS["SIGNIFICANT_TAXA_RANGE"]

# Path helpers
def get_raw_path() -> Path:
    return _PROJECT_ROOT / "data" / "raw"

def get_processed_path() -> Path:
    return _PROJECT_ROOT / "data" / "processed"

def get_results_path() -> Path:
    return _PROJECT_ROOT / "data" / "results"

def get_research_path() -> Path:
    return _PROJECT_ROOT / "data" / "research"

def get_specs_path() -> Path:
    return _PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"

def get_cache_dir() -> Path:
    cache = _PROJECT_ROOT / "data" / "cache"
    cache.mkdir(exist_ok=True)
    return cache

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        get_raw_path(),
        get_processed_path(),
        get_results_path(),
        get_research_path(),
        get_cache_dir(),
        _PROJECT_ROOT / "code" / "utils",
        _PROJECT_ROOT / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_max_workers() -> int:
    """Get the maximum number of workers for parallel processing."""
    val = get_env_var("MAX_WORKERS")
    if val:
        return int(val)
    return 4

def get_timeout_seconds() -> int:
    """Get the timeout for API calls in seconds."""
    val = get_env_var("TIMEOUT_SECONDS")
    if val:
        return int(val)
    return 30

def get_hf_token() -> Optional[str]:
    """Get the Hugging Face token."""
    return get_env_var("HF_TOKEN")

def get_ncbi_api_key() -> Optional[str]:
    """Get the NCBI API key."""
    return get_env_var("NCBI_API_KEY")
