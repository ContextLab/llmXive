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
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"
CONTRACTS_DIR = SPECS_DIR / "contracts"

# Configuration Defaults
RANDOM_SEED = 42
CLR_PSEUDOCOUNT = 1e-6
LOD_EXCLUDE_THRESHOLD = 0.0
MIN_SAMPLE_SIZE = 50
MAX_WORKERS = 4
TIMEOUT_SECONDS = 300
CACHE_DIR = DATA_DIR / "cache"

# SRA Configuration
# This is populated during the research phase (T010).
# For now, we set a default or rely on the environment variable.
SRA_ACCESSION = os.getenv("SRA_ACCESSION", "SRP000000") # Placeholder, will be set by T010

# HuggingFace Token
HF_TOKEN = os.getenv("HF_TOKEN")

# NCBI API Key
NCBI_API_KEY = os.getenv("NCBI_API_KEY")

def ensure_directories():
    """Create all necessary directories if they don't exist."""
    for dir_path in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, SPECS_DIR, CONTRACTS_DIR, CACHE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def get_raw_path():
    return RAW_DIR

def get_processed_path():
    return PROCESSED_DIR

def get_output_path():
    return RESULTS_DIR

def get_specs_path():
    return SPECS_DIR

def get_random_seed():
    return RANDOM_SEED

def get_pseudocount():
    return CLR_PSEUDOCOUNT

def get_impute_lod():
    return True

def get_lod_exclude_threshold():
    return LOD_EXCLUDE_THRESHOLD

def get_lod_handling_methods():
    return ["impute_half_lod", "exclude"]

def get_min_sample_size():
    return MIN_SAMPLE_SIZE

def get_hf_token():
    return HF_TOKEN

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
