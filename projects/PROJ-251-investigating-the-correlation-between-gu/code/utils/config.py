import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This ensures that variables defined in the project's .env file
# override default values or system environment variables.
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Paths
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_PATH = PROJECT_ROOT / "data" / "results"
SPECS_PATH = PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"
CONTRACTS_PATH = SPECS_PATH / "contracts"

# Ensure directories exist
def ensure_directories():
    """Create all necessary directories if they don't exist."""
    DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    DATA_RESULTS_PATH.mkdir(parents=True, exist_ok=True)
    SPECS_PATH.mkdir(parents=True, exist_ok=True)
    CONTRACTS_PATH.mkdir(parents=True, exist_ok=True)

def get_raw_path():
    return DATA_RAW_PATH

def get_processed_path():
    return DATA_PROCESSED_PATH

def get_output_path():
    return DATA_RESULTS_PATH

def get_specs_path():
    return SPECS_PATH

# Random seed for reproducibility
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))

# CLR transformation pseudocount
CLR_PSEUDOCOUNT = float(os.getenv("CLR_PSEUDOCOUNT", "1e-6"))

# LOD handling configuration
LOD_EXCLUDE_THRESHOLD = float(os.getenv("LOD_EXCLUDE_THRESHOLD", "0.0"))
LOD_HANDLING_METHODS = os.getenv("LOD_HANDLING_METHODS", "impute_fraction").split(",")
LOD_IMPUTE_FRACTION = float(os.getenv("LOD_IMPUTE_FRACTION", "0.5"))

# Minimum sample size requirement
MIN_SAMPLE_SIZE = int(os.getenv("MIN_SAMPLE_SIZE", "50"))

# SRA configuration
# This variable is populated during the research phase (T010)
# If not set in .env, it defaults to empty string, triggering synthetic fallback logic if configured
SRA_ACCESSION = os.getenv("SRA_ACCESSION", "")
USE_SYNTHETIC_DATA = os.getenv("USE_SYNTHETIC_DATA", "False").lower() == "true"

# API keys and tokens
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
SRA_TOKEN = os.getenv("SRA_TOKEN", "")

# Performance settings
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "300"))
CACHE_DIR = Path(os.getenv("CACHE_DIR", PROJECT_ROOT / "data" / "cache"))

# Success criteria
SEROCONVERSION_THRESHOLD = 4.0  # 4-fold rise
HAI_THRESHOLD = 40  # HAI titer >= 40

# Runtime limits
RUNTIME_LIMIT = 3600  # 1 hour in seconds
MEMORY_LIMIT_MB = 7340  # 7 GB in MB

def get_random_seed():
    return RANDOM_SEED

def get_pseudocount():
    return CLR_PSEUDOCOUNT

def get_impute_lod():
    return LOD_IMPUTE_FRACTION

def get_lod_exclude_threshold():
    return LOD_EXCLUDE_THRESHOLD

def get_lod_handling_methods():
    return LOD_HANDLING_METHODS

def get_min_sample_size():
    return MIN_SAMPLE_SIZE

def get_hf_token():
    return HUGGINGFACE_TOKEN

def get_ncbi_api_key():
    return NCBI_API_KEY

def get_sra_accession():
    return SRA_ACCESSION

def get_max_workers():
    return MAX_WORKERS

def get_timeout_seconds():
    return TIMEOUT_SECONDS

def get_cache_dir():
    return CACHE_DIR