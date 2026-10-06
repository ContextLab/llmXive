import os
import json
from pathlib import Path
from typing import Optional

class Config:
    """Central configuration for the project."""
    
    # Project root
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Directories
    DATA_DIR = PROJECT_ROOT / "data"
    DATA_RAW_DIR = DATA_DIR / "raw"
    DATA_INTERMEDIATE_DIR = DATA_DIR / "intermediate"
    DATA_PROCESSED_DIR = DATA_DIR / "processed"
    DATA_PROVENANCE_DIR = DATA_DIR / "provenance"
    DATA_RESULTS_DIR = DATA_DIR / "results"
    CODE_DIR = PROJECT_ROOT / "code"
    TESTS_DIR = PROJECT_ROOT / "tests"
    
    # Contracts
    CONTRACTS_DIR = PROJECT_ROOT / "contracts"
    OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"
    DATASET_SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
    
    # State
    STATE_DIR = PROJECT_ROOT / "state"
    PROJECTS_STATE_DIR = STATE_DIR / "projects"
    
    # Paths for artifacts
    MERGED_CSV_PATH = DATA_INTERMEDIATE_DIR / "merged.csv"
    DFT_QUERIES_PATH = DATA_PROVENANCE_DIR / "dft_queries.jsonl"
    CHECKSUMS_PATH = DATA_PROVENANCE_DIR / "checksums.txt"
    EVALUATION_RESULTS_PATH = DATA_RESULTS_DIR / "evaluation_results.json"
    CORRELATION_RESULTS_PATH = DATA_RESULTS_DIR / "correlation_results.json"
    BOOTSTRAP_RESULTS_PATH = DATA_RESULTS_DIR / "bootstrap_stability.json"
    SHAP_RESULTS_PATH = DATA_RESULTS_DIR / "shap_results.json"
    OUTPUT_JSON_PATH = DATA_RESULTS_DIR / "output.json"
    
    # API Keys
    MP_API_KEY = os.getenv("MP_API_KEY", None)
    
    # Experimental data URL
    EXPERIMENTAL_DATA_URL = "https://matnavi.nims.go.jp/api/v1/datasets/bcc_steel_yield_strength"
    
    # Random seed
    RANDOM_SEED = 42
    
    # Error codes
    ERR_INSUFFICIENT_DATA = "ERR_INSUFFICIENT_DATA"
    ERR_API_FAILURE = "ERR_API_FAILURE"
    ERR_SCHEMA_VALIDATION = "ERR_SCHEMA_VALIDATION"
    
    # Modeling parameters
    N_FOLDS = 5
    N_ESTIMATORS = 100
    MAX_DEPTH = 10
    
    # Bootstrap parameters
    N_BOOTSTRAP_SAMPLES = 10
    MIN_SAMPLE_SIZE = 10
    MAX_SAMPLE_SIZE = 50

# Global config instance
CONFIG = Config()

def ensure_dirs():
    """Ensure all required directories exist."""
    dirs = [
        CONFIG.DATA_DIR,
        CONFIG.DATA_RAW_DIR,
        CONFIG.DATA_INTERMEDIATE_DIR,
        CONFIG.DATA_PROCESSED_DIR,
        CONFIG.DATA_PROVENANCE_DIR,
        CONFIG.DATA_RESULTS_DIR,
        CONFIG.CONTRACTS_DIR,
        CONFIG.STATE_DIR,
        CONFIG.PROJECTS_STATE_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_mp_api_key() -> Optional[str]:
    """Get the Materials Project API key."""
    return CONFIG.MP_API_KEY

if __name__ == "__main__":
    ensure_dirs()
    print("Directories ensured.")
