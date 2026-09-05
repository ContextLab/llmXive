"""
Configuration module for the gut microbiome and influenza vaccination study.

This module provides centralized access to configuration parameters, including
paths, seeds, thresholds, and data source settings.
"""
import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default values for configuration
DEFAULTS = {
    'SRA_ACCESSION': None,
    'LOD_VALUE': 10.0,
    'SEROCONVERSION_THRESHOLD': 4.0,
    'HAI_THRESHOLD': 40,
    'MIN_SAMPLE_SIZE': 50,
    'USE_SYNTHETIC_DATA': False,
    'RANDOM_SEED': 42,
    'PSEUDOCOUNT': 1e-6,
    'SIGNIFICANT_TAXA_RANGE': (1, 10),  # Expected range for significant taxa
}

def get_env_var(key: str, default: Any = None) -> Any:
    """Get an environment variable with a default fallback."""
    value = os.getenv(key)
    if value is None:
        return default
    # Try to convert to appropriate type
    if value.lower() in ('true', 'yes', '1'):
        return True
    elif value.lower() in ('false', 'no', '0'):
        return False
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value

def get_sra_accession() -> Optional[str]:
    """Get the SRA accession ID from environment or config."""
    return get_env_var('SRA_ACCESSION', DEFAULTS['SRA_ACCESSION'])

def get_lod_value() -> float:
    """Get the Limit of Detection (LOD) value for titer measurements."""
    return get_env_var('LOD_VALUE', DEFAULTS['LOD_VALUE'])

def get_impute_lod() -> float:
    """Get the value used for imputing LOD measurements (0.5 * LOD)."""
    return 0.5 * get_lod_value()

def get_lod_handling_methods() -> List[str]:
    """Get the list of methods for handling LOD values."""
    return ['impute', 'exclude']

def get_min_sample_size() -> int:
    """Get the minimum required sample size."""
    return get_env_var('MIN_SAMPLE_SIZE', DEFAULTS['MIN_SAMPLE_SIZE'])

def get_use_synthetic_data() -> bool:
    """Get the flag indicating whether to use synthetic data."""
    return get_env_var('USE_SYNTHETIC_DATA', DEFAULTS['USE_SYNTHETIC_DATA'])

def get_random_seed() -> int:
    """Get the random seed for reproducibility."""
    return get_env_var('RANDOM_SEED', DEFAULTS['RANDOM_SEED'])

def get_pseudocount() -> float:
    """Get the pseudo-count value for CLR transformation."""
    return get_env_var('PSEUDOCOUNT', DEFAULTS['PSEUDOCOUNT'])

def get_seroconversion_threshold() -> float:
    """Get the threshold for defining seroconversion (fold rise)."""
    return get_env_var('SEROCONVERSION_THRESHOLD', DEFAULTS['SEROCONVERSION_THRESHOLD'])

def get_hai_threshold() -> int:
    """Get the threshold for defining response based on absolute HAI titer."""
    return get_env_var('HAI_THRESHOLD', DEFAULTS['HAI_THRESHOLD'])

def get_significant_taxa_range() -> tuple:
    """Get the expected range for the number of significant taxa."""
    val = get_env_var('SIGNIFICANT_TAXA_RANGE')
    if val and isinstance(val, str):
        parts = val.strip('()').split(',')
        return (int(parts[0]), int(parts[1]))
    return DEFAULTS['SIGNIFICANT_TAXA_RANGE']

def get_raw_path() -> Path:
    """Get the path to the raw data directory."""
    return PROJECT_ROOT / 'data' / 'raw'

def get_processed_path() -> Path:
    """Get the path to the processed data directory."""
    return PROJECT_ROOT / 'data' / 'processed'

def get_results_path() -> Path:
    """Get the path to the results directory."""
    return PROJECT_ROOT / 'data' / 'results'

def get_research_path() -> Path:
    """Get the path to the research data directory."""
    return PROJECT_ROOT / 'data' / 'research'

def get_specs_path() -> Path:
    """Get the path to the specifications directory."""
    return PROJECT_ROOT / 'specs' / '001-investigating-the-correlation-between-gu'

def get_cache_dir() -> Path:
    """Get the path to the cache directory."""
    cache_dir = PROJECT_ROOT / '.cache'
    cache_dir.mkdir(exist_ok=True)
    return cache_dir

def get_hf_token() -> Optional[str]:
    """Get the Hugging Face token from environment."""
    return os.getenv('HF_TOKEN')

def get_ncbi_api_key() -> Optional[str]:
    """Get the NCBI API key from environment."""
    return os.getenv('NCBI_API_KEY')

def get_max_workers() -> int:
    """Get the maximum number of worker threads/processes."""
    return get_env_var('MAX_WORKERS', 4)

def get_timeout_seconds() -> int:
    """Get the timeout in seconds for network operations."""
    return get_env_var('TIMEOUT_SECONDS', 300)

def ensure_directories():
    """Ensure all required directories exist."""
    for path_func in [get_raw_path, get_processed_path, get_results_path, get_research_path]:
        path = path_func()
        path.mkdir(parents=True, exist_ok=True)

# Initialize directories on module import
ensure_directories()
