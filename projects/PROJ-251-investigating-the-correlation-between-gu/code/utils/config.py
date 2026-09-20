import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CODE_DIR = BASE_DIR / "code"
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
RESEARCH_DIR = DATA_DIR / "research"
SPECS_DIR = BASE_DIR / "specs"

# Configuration Values
SRA_ACCESSION = os.getenv("SRA_ACCESSION", None)
LOD_VALUE = float(os.getenv("LOD_VALUE", "10.0")) if os.getenv("LOD_VALUE") else None
SEROCONVERSION_THRESHOLD = float(os.getenv("SEROCONVERSION_THRESHOLD", "4.0"))
HAI_THRESHOLD = float(os.getenv("HAI_THRESHOLD", "40.0"))
USE_SYNTHETIC_DATA = os.getenv("USE_SYNTHETIC_DATA", "False").lower() == "true"
NUM_SYNTHETIC_TAXA = int(os.getenv("NUM_SYNTHETIC_TAXA", "20"))
TARGET_CORRELATION = float(os.getenv("TARGET_CORRELATION", "0.5"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
MIN_SAMPLE_SIZE = int(os.getenv("MIN_SAMPLE_SIZE", "50"))
PSEUDOCOUNT = float(os.getenv("PSEUDOCOUNT", "1e-6"))
SIGNIFICANT_TAXA_RANGE = os.getenv("SIGNIFICANT_TAXA_RANGE", "1-10")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "7200"))

def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, default)

def get_lod_value() -> Optional[float]:
    return LOD_VALUE

def get_lod_handling_methods() -> List[str]:
    return ["impute"]

def get_impute_lod() -> float:
    return 0.5 * LOD_VALUE if LOD_VALUE else 0.0

def get_seroconversion_threshold() -> float:
    return SEROCONVERSION_THRESHOLD

def get_hai_threshold() -> float:
    return HAI_THRESHOLD

def get_sra_accession() -> Optional[str]:
    return SRA_ACCESSION

def get_use_synthetic_data() -> bool:
    return USE_SYNTHETIC_DATA

def get_num_synthetic_taxa() -> int:
    return NUM_SYNTHETIC_TAXA

def get_target_correlation() -> float:
    return TARGET_CORRELATION

def get_random_seed() -> int:
    return RANDOM_SEED

def get_min_sample_size() -> int:
    return MIN_SAMPLE_SIZE

def get_pseudocount() -> float:
    return PSEUDOCOUNT

def get_significant_taxa_range() -> str:
    return SIGNIFICANT_TAXA_RANGE

def get_raw_path() -> Path:
    return RAW_DIR

def get_processed_path() -> Path:
    return PROCESSED_DIR

def get_results_path() -> Path:
    return RESULTS_DIR

def get_research_path() -> Path:
    return RESEARCH_DIR

def get_specs_path() -> Path:
    return SPECS_DIR

def get_cache_dir() -> Path:
    cache = BASE_DIR / ".cache"
    cache.mkdir(exist_ok=True)
    return cache

def ensure_directories():
    for d in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, RESEARCH_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def get_max_workers() -> int:
    return MAX_WORKERS

def get_timeout_seconds() -> int:
    return TIMEOUT_SECONDS

def get_hf_token() -> Optional[str]:
    return os.getenv("HF_TOKEN")

def get_ncbi_api_key() -> Optional[str]:
    return os.getenv("NCBI_API_KEY")
