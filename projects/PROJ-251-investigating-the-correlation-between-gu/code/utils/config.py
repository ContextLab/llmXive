import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Paths
RAW_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
RESULTS_PATH = PROJECT_ROOT / "data" / "results"
RESEARCH_PATH = PROJECT_ROOT / "data" / "research"
SPECS_PATH = PROJECT_ROOT / "specs"
CODE_PATH = PROJECT_ROOT / "code"
TESTS_PATH = PROJECT_ROOT / "tests"

def ensure_directories():
    """Ensure all required directories exist."""
    for path in [RAW_PATH, PROCESSED_PATH, RESULTS_PATH, RESEARCH_PATH, SPECS_PATH, CODE_PATH, TESTS_PATH]:
        path.mkdir(parents=True, exist_ok=True)

# Configuration values
def get_random_seed() -> int:
    return int(os.getenv("RANDOM_SEED", "42"))

def get_pseudocount() -> float:
    return float(os.getenv("CLR_PSEUDOCOUNT", "1e-6"))

def get_lod_value() -> Optional[float]:
    val = os.getenv("LOD_VALUE")
    return float(val) if val else None

def get_impute_lod() -> float:
    """Default imputation value for LOD (0.5 * LOD_VALUE or 0.5 * 10.0 if not set)."""
    lod = get_lod_value()
    if lod is None:
        return 5.0 # 0.5 * 10.0
    return 0.5 * lod

def get_lod_handling_methods() -> List[str]:
    return ["impute", "exclude"]

def get_min_sample_size() -> int:
    return int(os.getenv("MIN_SAMPLE_SIZE", "50"))

def get_sra_accession() -> Optional[str]:
    return os.getenv("SRA_ACCESSION")

def get_use_synthetic_data() -> bool:
    val = os.getenv("USE_SYNTHETIC_DATA", "false")
    return val.lower() in ("true", "1", "yes")

def get_hf_token() -> Optional[str]:
    return os.getenv("HF_TOKEN")

def get_ncbi_api_key() -> Optional[str]:
    return os.getenv("NCBI_API_KEY")

def get_max_workers() -> int:
    return int(os.getenv("MAX_WORKERS", "4"))

def get_timeout_seconds() -> int:
    return int(os.getenv("TIMEOUT_SECONDS", "300"))

def get_cache_dir() -> Path:
    return Path(os.getenv("CACHE_DIR", PROJECT_ROOT / "data" / "cache"))

def get_raw_path() -> Path:
    return RAW_PATH

def get_processed_path() -> Path:
    return PROCESSED_PATH

def get_output_path() -> Path:
    return RESULTS_PATH

def get_specs_path() -> Path:
    return SPECS_PATH

def get_research_path() -> Path:
    return RESEARCH_PATH

def get_seroconversion_threshold() -> float:
    return float(os.getenv("SEROCONVERSION_THRESHOLD", "4.0"))

def get_hai_threshold() -> float:
    return float(os.getenv("HAI_THRESHOLD", "40.0"))

def get_significant_taxa_range() -> tuple:
    # Returns (min, max) expected range for significant taxa count
    return (1, 9)
