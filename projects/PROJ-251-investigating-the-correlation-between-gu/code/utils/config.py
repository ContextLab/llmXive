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

# Paths
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
DATA_RESEARCH = PROJECT_ROOT / "data" / "research"
CODE_DIR = PROJECT_ROOT / "code"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"

# Configuration values with defaults
_DEFAULTS = {
    "SRA_ACCESSION": None,
    "LOD_VALUE": 10.0,
    "SEROCONVERSION_THRESHOLD": 4.0,
    "NUM_SYNTHETIC_TAXA": 5,
    "TARGET_CORRELATION": 0.6,
    "USE_SYNTHETIC_DATA": False,
    "RANDOM_SEED": 42,
    "MIN_SAMPLE_SIZE": 50,
    "PSEUDOCOUNT": 1e-6,
    "HAI_THRESHOLD": 40.0,
    "SIGNIFICANT_TAXA_RANGE": [2, 10],
}

def get_env_var(key: str, default: Any = None) -> Any:
    """Retrieve an environment variable with a default fallback."""
    return os.getenv(key, default)

def get_sra_accession() -> Optional[str]:
    """Get the SRA accession ID from config or env."""
    val = os.getenv("SRA_ACCESSION")
    if val:
        return val
    return _DEFAULTS.get("SRA_ACCESSION")

def get_lod_value() -> float:
    """Get the Limit of Detection value."""
    val = os.getenv("LOD_VALUE")
    if val:
        return float(val)
    return _DEFAULTS["LOD_VALUE"]

def get_impute_lod() -> float:
    """Get the imputation factor for LOD (default 0.5)."""
    val = os.getenv("IMPUTE_LOD_FACTOR")
    if val:
        return float(val)
    return 0.5

def get_lod_handling_methods() -> List[str]:
    """Get list of LOD handling methods."""
    val = os.getenv("LOD_HANDLING_METHODS")
    if val:
        return val.split(",")
    return ["impute_0.5"]

def get_min_sample_size() -> int:
    """Get minimum required sample size."""
    val = os.getenv("MIN_SAMPLE_SIZE")
    if val:
        return int(val)
    return _DEFAULTS["MIN_SAMPLE_SIZE"]

def get_use_synthetic_data() -> bool:
    """Check if synthetic data should be used."""
    val = os.getenv("USE_SYNTHETIC_DATA")
    if val is not None:
        return val.lower() in ("true", "1", "yes")
    return _DEFAULTS["USE_SYNTHETIC_DATA"]

def get_random_seed() -> int:
    """Get the random seed for reproducibility."""
    val = os.getenv("RANDOM_SEED")
    if val:
        return int(val)
    return _DEFAULTS["RANDOM_SEED"]

def get_num_synthetic_taxa() -> int:
    """Get the number of synthetic taxa to generate."""
    val = os.getenv("NUM_SYNTHETIC_TAXA")
    if val:
        return int(val)
    return _DEFAULTS["NUM_SYNTHETIC_TAXA"]

def get_target_correlation() -> float:
    """Get the target correlation for synthetic data."""
    val = os.getenv("TARGET_CORRELATION")
    if val:
        return float(val)
    return _DEFAULTS["TARGET_CORRELATION"]

def get_pseudocount() -> float:
    """Get the pseudocount value for CLR transformation."""
    val = os.getenv("PSEUDOCOUNT")
    if val:
        return float(val)
    return _DEFAULTS["PSEUDOCOUNT"]

def get_seroconversion_threshold() -> float:
    """Get the seroconversion threshold (fold rise)."""
    val = os.getenv("SEROCONVERSION_THRESHOLD")
    if val:
        return float(val)
    return _DEFAULTS["SEROCONVERSION_THRESHOLD"]

def get_hai_threshold() -> float:
    """Get the absolute HAI titer threshold."""
    val = os.getenv("HAI_THRESHOLD")
    if val:
        return float(val)
    return _DEFAULTS["HAI_THRESHOLD"]

def get_significant_taxa_range() -> List[int]:
    """Get the expected range of significant taxa for real data."""
    val = os.getenv("SIGNIFICANT_TAXA_RANGE")
    if val:
        parts = val.split(",")
        return [int(p) for p in parts]
    return _DEFAULTS["SIGNIFICANT_TAXA_RANGE"]

def get_raw_path() -> Path:
    """Get the path to the raw data directory."""
    return DATA_RAW

def get_processed_path() -> Path:
    """Get the path to the processed data directory."""
    return DATA_PROCESSED

def get_results_path() -> Path:
    """Get the path to the results directory."""
    return DATA_RESULTS

def get_research_path() -> Path:
    """Get the path to the research data directory."""
    return DATA_RESEARCH

def get_specs_path() -> Path:
    """Get the path to the specs directory."""
    return SPECS_DIR

def get_cache_dir() -> Path:
    """Get the cache directory path."""
    cache = os.getenv("CACHE_DIR")
    if cache:
        return Path(cache)
    return PROJECT_ROOT / ".cache"

def get_hf_token() -> Optional[str]:
    """Get the Hugging Face token."""
    return os.getenv("HF_TOKEN")

def get_ncbi_api_key() -> Optional[str]:
    """Get the NCBI API key."""
    return os.getenv("NCBI_API_KEY")

def get_max_workers() -> int:
    """Get the maximum number of workers for parallel processing."""
    val = os.getenv("MAX_WORKERS")
    if val:
        return int(val)
    return 4

def get_timeout_seconds() -> int:
    """Get the timeout for network requests in seconds."""
    val = os.getenv("TIMEOUT_SECONDS")
    if val:
        return int(val)
    return 30

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [DATA_RAW, DATA_PROCESSED, DATA_RESULTS, DATA_RESEARCH, CODE_DIR, SPECS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
