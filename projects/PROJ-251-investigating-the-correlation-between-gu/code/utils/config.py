import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Paths
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"

# Configuration Defaults
RANDOM_SEED = 42
CLR_PSEUDOCOUNT = 1e-6
LOD_EXCLUDE_THRESHOLD = 0.0
LOD_HANDLING_METHODS = ["impute_fraction", "exclude"]
MIN_SAMPLE_SIZE = 50
SEROCONVERSION_THRESHOLD = 4.0
HAI_THRESHOLD = 40
RUNTIME_LIMIT = 300  # seconds
MAX_MEMORY_MB = 7340  # 7 GB

# Data Source Config
SRA_ACCESSION = os.getenv("SRA_ACCESSION", "")
USE_SYNTHETIC_DATA = os.getenv("USE_SYNTHETIC_DATA", "False").lower() == "true"
HF_TOKEN = os.getenv("HF_TOKEN", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "300"))
CACHE_DIR = Path(os.getenv("CACHE_DIR", PROJECT_ROOT / ".cache"))

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR, SPECS_DIR]
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
    return RANDOM_SEED

def get_pseudocount() -> float:
    return CLR_PSEUDOCOUNT

def get_impute_lod() -> bool:
    return os.getenv("IMPUTE_LOD", "True").lower() == "true"

def get_lod_exclude_threshold() -> float:
    return LOD_EXCLUDE_THRESHOLD

def get_lod_handling_methods() -> List[str]:
    return LOD_HANDLING_METHODS

def get_min_sample_size() -> int:
    return MIN_SAMPLE_SIZE

def get_hf_token() -> str:
    return HF_TOKEN

def get_ncbi_api_key() -> str:
    return NCBI_API_KEY

def get_sra_accession() -> str:
    return SRA_ACCESSION

def get_max_workers() -> int:
    return MAX_WORKERS

def get_timeout_seconds() -> int:
    return TIMEOUT_SECONDS

def get_cache_dir() -> Path:
    return CACHE_DIR

def get_use_synthetic_data() -> bool:
    return USE_SYNTHETIC_DATA
