"""
Configuration module for the Gut Microbiome - Influenza Vaccination study.

This module provides centralized configuration management including:
- File paths
- Random seeds
- Thresholds
- Feature flags (USE_SYNTHETIC_DATA)
"""
import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory (assumes code/ is at project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Directory paths
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_RESULTS = DATA_DIR / "results"
DATA_RESEARCH = DATA_DIR / "research"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"
CONTRACTS_DIR = SPECS_DIR / "contracts"

# Ensure directories exist
def ensure_directories():
    """Create all required directories if they don't exist."""
    dirs = [DATA_RAW, DATA_PROCESSED, DATA_RESULTS, DATA_RESEARCH, CONTRACTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Random seed for reproducibility
def get_random_seed() -> int:
    """Get the random seed for reproducibility."""
    seed_str = os.getenv("RANDOM_SEED")
    if seed_str:
        return int(seed_str)
    return 42

# Pseudocount for CLR transformation
def get_pseudocount() -> float:
    """Get the pseudocount value for CLR transformation."""
    return float(os.getenv("CLR_PSEUDOCOUNT", "1e-6"))

# LOD handling configuration
def get_impute_lod() -> bool:
    """Whether to impute values below LOD."""
    return os.getenv("IMPUTE_LOD", "true").lower() == "true"

def get_lod_exclude_threshold() -> float:
    """Threshold for excluding LOD values."""
    return float(os.getenv("LOD_EXCLUDE_THRESHOLD", "0.0"))

def get_lod_handling_methods() -> List[str]:
    """List of LOD handling methods to try."""
    methods = os.getenv("LOD_HANDLING_METHODS", "half_lod,zero")
    return [m.strip() for m in methods.split(",")]

# Minimum sample size requirement
def get_min_sample_size() -> int:
    """Minimum number of subjects required."""
    return int(os.getenv("MIN_SAMPLE_SIZE", "50"))

# SRA accession for real data
def get_sra_accession() -> Optional[str]:
    """Get the SRA accession ID for real data."""
    return os.getenv("SRA_ACCESSION")

# Use synthetic data flag
def get_use_synthetic_data() -> bool:
    """Check if synthetic data should be used."""
    return os.getenv("USE_SYNTHETIC_DATA", "false").lower() == "true"

# API keys and tokens
def get_hf_token() -> Optional[str]:
    """Get HuggingFace token."""
    return os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")

def get_ncbi_api_key() -> Optional[str]:
    """Get NCBI API key."""
    return os.getenv("NCBI_API_KEY")

# Worker and timeout configuration
def get_max_workers() -> int:
    """Maximum number of worker processes."""
    return int(os.getenv("MAX_WORKERS", "4"))

def get_timeout_seconds() -> int:
    """Timeout in seconds for downloads."""
    return int(os.getenv("TIMEOUT_SECONDS", "300"))

# Cache directory
def get_cache_dir() -> Path:
    """Get cache directory path."""
    cache_path = os.getenv("CACHE_DIR")
    if cache_path:
        return Path(cache_path)
    return DATA_DIR / "cache"

# Path getters
def get_raw_path() -> Path:
    """Get path to raw data directory."""
    return DATA_RAW

def get_processed_path() -> Path:
    """Get path to processed data directory."""
    return DATA_PROCESSED

def get_output_path() -> Path:
    """Get path to results directory."""
    return DATA_RESULTS

def get_specs_path() -> Path:
    """Get path to specs directory."""
    return SPECS_DIR

# Seroconversion and response thresholds
def get_seroconversion_threshold() -> float:
    """Threshold for seroconversion (4-fold rise)."""
    return float(os.getenv("SEROCONVERSION_THRESHOLD", "4.0"))

def get_hai_threshold() -> float:
    """HAI titer threshold for response."""
    return float(os.getenv("HAI_THRESHOLD", "40.0"))

# Runtime limits
def get_runtime_limit() -> int:
    """Maximum runtime in seconds."""
    return int(os.getenv("RUNTIME_LIMIT", "3600"))

# Significant taxa range
def get_significant_taxa_range() -> tuple:
    """Expected range of significant taxa count."""
    range_str = os.getenv("SIGNIFICANT_TAXA_RANGE", "1,9")
    parts = range_str.split(",")
    return (int(parts[0]), int(parts[1]))

# Initialize directories on import
ensure_directories()

# Export all public functions
__all__ = [
    'ensure_directories',
    'get_raw_path',
    'get_processed_path',
    'get_output_path',
    'get_specs_path',
    'get_random_seed',
    'get_pseudocount',
    'get_impute_lod',
    'get_lod_exclude_threshold',
    'get_lod_handling_methods',
    'get_min_sample_size',
    'get_hf_token',
    'get_ncbi_api_key',
    'get_sra_accession',
    'get_max_workers',
    'get_timeout_seconds',
    'get_cache_dir',
    'get_use_synthetic_data',
    'get_seroconversion_threshold',
    'get_hai_threshold',
    'get_runtime_limit',
    'get_significant_taxa_range',
]