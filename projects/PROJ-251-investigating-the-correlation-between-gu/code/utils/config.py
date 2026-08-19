import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data paths
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"

# Configuration defaults
DEFAULT_SEED = 42
DEFAULT_PSEUDOCOUNT = 1e-6
DEFAULT_LOD_EXCLUDE_THRESHOLD = 0.0
DEFAULT_MIN_SAMPLE_SIZE = 50
DEFAULT_RUNTIME_LIMIT = 300  # seconds
DEFAULT_MAX_WORKERS = 4
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_CACHE_DIR = PROJECT_ROOT / ".cache"

# SRA configuration
SRA_ACCESSION = os.getenv("SRA_ACCESSION", "")
USE_SYNTHETIC_DATA = os.getenv("USE_SYNTHETIC_DATA", "false").lower() == "true"

# API keys
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")

# LOD handling
LOD_EXCLUDE_THRESHOLD = float(os.getenv("LOD_EXCLUDE_THRESHOLD", DEFAULT_LOD_EXCLUDE_THRESHOLD))
LOD_HANDLING_METHODS = os.getenv("LOD_HANDLING_METHODS", "impute_fraction").split(",")

# Significance thresholds
SIGNIFICANT_TAXA_RANGE = [1, 9]
SEROCONVERSION_THRESHOLD = 4.0
HAI_THRESHOLD = 40.0

# Runtime limits
RUNTIME_LIMIT = int(os.getenv("RUNTIME_LIMIT", DEFAULT_RUNTIME_LIMIT))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", DEFAULT_MAX_WORKERS))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DIR,
        SPECS_DIR,
        PROJECT_ROOT / "code" / "utils",
        PROJECT_ROOT / "data" / "research"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_raw_path() -> Path:
    return RAW_DATA_DIR

def get_processed_path() -> Path:
    return PROCESSED_DATA_DIR

def get_output_path() -> Path:
    return RESULTS_DIR

def get_specs_path() -> Path:
    return SPECS_DIR

def get_random_seed() -> int:
    return DEFAULT_SEED

def get_pseudocount() -> float:
    return DEFAULT_PSEUDOCOUNT

def get_impute_lod() -> bool:
    return "impute_fraction" in LOD_HANDLING_METHODS

def get_lod_exclude_threshold() -> float:
    return LOD_EXCLUDE_THRESHOLD

def get_lod_handling_methods() -> List[str]:
    return LOD_HANDLING_METHODS

def get_min_sample_size() -> int:
    return DEFAULT_MIN_SAMPLE_SIZE

def get_hf_token() -> str:
    return HUGGINGFACE_TOKEN

def get_ncbi_api_key() -> str:
    return NCBI_API_KEY

def get_sra_accession() -> str:
    return SRA_ACCESSION

def get_max_workers() -> int:
    return MAX_WORKERS

def get_timeout_seconds() -> int:
    return TIMEOUT_SECONDS

def get_cache_dir() -> Path:
    return DEFAULT_CACHE_DIR

def get_use_synthetic_data() -> bool:
    return USE_SYNTHETIC_DATA
