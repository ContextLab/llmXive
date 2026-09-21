import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
DATA_RESEARCH = PROJECT_ROOT / "data" / "research"
CODE_ROOT = PROJECT_ROOT / "code"
SPECS_ROOT = PROJECT_ROOT / "specs" / "001-investigating-the-correlation-between-gu"

# Configuration getters
def get_env_var(key: str, default=None):
    return os.getenv(key, default)

def get_sra_accession():
    return get_env_var("SRA_ACCESSION")

def get_use_synthetic_data():
    val = get_env_var("USE_SYNTHETIC_DATA", "false").lower()
    return val in ("true", "1", "yes")

def get_lod_value():
    val = get_env_var("LOD_VALUE")
    if val is None:
        return None
    try:
        return float(val)
    except ValueError:
        return None

def get_seroconversion_threshold():
    val = get_env_var("SEROCONVERSION_THRESHOLD", "4.0")
    return float(val)

def get_hai_threshold():
    val = get_env_var("HAI_THRESHOLD", "40.0")
    return float(val)

def get_num_synthetic_taxa():
    val = get_env_var("NUM_SYNTHETIC_TAXA", "20")
    return int(val)

def get_target_correlation():
    val = get_env_var("TARGET_CORRELATION", "0.3")
    return float(val)

def get_random_seed():
    val = get_env_var("RANDOM_SEED", "42")
    return int(val)

def get_min_sample_size():
    val = get_env_var("MIN_SAMPLE_SIZE", "50")
    return int(val)

def get_pseudocount():
    val = get_env_var("PSEUDOCOUNT", "1e-6")
    return float(val)

def get_significant_taxa_range():
    # Expected range for SC-004 (min, max)
    val = get_env_var("SIGNIFICANT_TAXA_RANGE", "1,9")
    parts = val.split(",")
    return int(parts[0]), int(parts[1])

# Path helpers
def get_raw_path(filename):
    return DATA_RAW / filename

def get_processed_path(filename):
    return DATA_PROCESSED / filename

def get_results_path(filename):
    return DATA_RESULTS / filename

def get_research_path(filename):
    return DATA_RESEARCH / filename

def get_specs_pat():
    return SPECS_ROOT
