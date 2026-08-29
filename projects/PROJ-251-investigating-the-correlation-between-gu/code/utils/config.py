import os
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Configuration defaults
DEFAULT_SEED = 42
DEFAULT_PSEUDOCOUNT = 1e-6
DEFAULT_LOD = 10.0
DEFAULT_LOD_HANDLING = "impute"  # Options: "impute", "exclude"
DEFAULT_MIN_SAMPLE_SIZE = 50
DEFAULT_SEROCONVERSION_THRESHOLD = 4.0
DEFAULT_HAI_THRESHOLD = 40.0
DEFAULT_RUNTIME_LIMIT = 5400  # 1.5 hours in seconds
DEFAULT_SIGNIFICANT_TAXA_RANGE = (1, 9)

def get_random_seed() -> int:
    """Get random seed from environment or use default."""
    return int(os.getenv("RANDOM_SEED", DEFAULT_SEED))

def get_pseudocount() -> float:
    """Get CLR pseudocount from environment or use default."""
    return float(os.getenv("CLR_PSEUDOCOUNT", DEFAULT_PSEUDOCOUNT))

def get_impute_lod() -> float:
    """Get LOD imputation value from environment or use default."""
    return float(os.getenv("LOD_VALUE", DEFAULT_LOD))

def get_lod_exclude_threshold() -> float:
    """Get LOD exclusion threshold from environment."""
    return float(os.getenv("LOD_EXCLUDE_THRESHOLD", 0.0))

def get_lod_handling_methods() -> List[str]:
    """Get list of LOD handling methods."""
    methods = os.getenv("LOD_HANDLING_METHODS", DEFAULT_LOD_HANDLING)
    return [m.strip() for m in methods.split(",")]

def get_min_sample_size() -> int:
    """Get minimum sample size from environment or use default."""
    return int(os.getenv("MIN_SAMPLE_SIZE", DEFAULT_MIN_SAMPLE_SIZE))

def get_sra_accession() -> Optional[str]:
    """Get SRA accession from environment."""
    return os.getenv("SRA_ACCESSION")

def get_use_synthetic_data() -> bool:
    """Check if synthetic data should be used."""
    val = os.getenv("USE_SYNTHETIC_DATA", "false").lower()
    return val in ("true", "1", "yes")

def get_hf_token() -> Optional[str]:
    """Get Hugging Face token from environment."""
    return os.getenv("HF_TOKEN")

def get_ncbi_api_key() -> Optional[str]:
    """Get NCBI API key from environment."""
    return os.getenv("NCBI_API_KEY")

def get_max_workers() -> int:
    """Get maximum number of workers from environment."""
    return int(os.getenv("MAX_WORKERS", 4))

def get_timeout_seconds() -> int:
    """Get timeout in seconds for operations."""
    return int(os.getenv("TIMEOUT_SECONDS", 3600))

def get_cache_dir() -> Path:
    """Get cache directory path."""
    cache_path = os.getenv("CACHE_DIR", str(PROJECT_ROOT / "data" / "cache"))
    return Path(cache_path)

def get_raw_path() -> Path:
    """Get raw data directory path."""
    return PROJECT_ROOT / "data" / "raw"

def get_processed_path() -> Path:
    """Get processed data directory path."""
    return PROJECT_ROOT / "data" / "processed"

def get_output_path() -> Path:
    """Get results output directory path."""
    return PROJECT_ROOT / "data" / "results"

def get_specs_path() -> Path:
    """Get specs directory path."""
    return PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"

def get_seroconversion_threshold() -> float:
    """Get seroconversion threshold."""
    return float(os.getenv("SEROCONVERSION_THRESHOLD", DEFAULT_SEROCONVERSION_THRESHOLD))

def get_hai_threshold() -> float:
    """Get HAI threshold."""
    return float(os.getenv("HAI_THRESHOLD", DEFAULT_HAI_THRESHOLD))

def get_runtime_limit() -> int:
    """Get runtime limit in seconds."""
    return int(os.getenv("RUNTIME_LIMIT", DEFAULT_RUNTIME_LIMIT))

def get_significant_taxa_range() -> tuple:
    """Get expected range of significant taxa."""
    range_str = os.getenv("SIGNIFICANT_TAXA_RANGE", f"{DEFAULT_SIGNIFICANT_TAXA_RANGE[0]},{DEFAULT_SIGNIFICANT_TAXA_RANGE[1]}")
    parts = [int(x.strip()) for x in range_str.split(",")]
    return tuple(parts)

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        get_raw_path(),
        get_processed_path(),
        get_output_path(),
        get_cache_dir(),
        PROJECT_ROOT / "code" / "tests",
        PROJECT_ROOT / "contracts"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
