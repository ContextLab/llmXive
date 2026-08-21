import os
from pathlib import Path
from typing import Optional

# Project root is assumed to be the directory containing this file's parent
# When running as a module, we resolve relative to the file location
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configuration parameters
OPTICAL_FLOW_THRESHOLD: float = 0.5
EMBEDDING_DIM: int = 4096
MAX_MEMORY_GB: float = 6.0
MEMORY_WARNING_THRESHOLD: float = 0.8
MEMORY_CRITICAL_THRESHOLD: float = 0.9
VALIDATION_THRESHOLD: float = 0.90
SEED: int = 42

# Path constants derived from project root
DATA_RAW_DIR: Path = _PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED_DIR: Path = _PROJECT_ROOT / 'data' / 'processed'
DATA_VALIDATION_DIR: Path = _PROJECT_ROOT / 'data' / 'validation'
DATA_MODELS_DIR: Path = _PROJECT_ROOT / 'data' / 'models'
DATA_RESULTS_DIR: Path = _PROJECT_ROOT / 'data' / 'results'
DATA_LOGS_DIR: Path = _PROJECT_ROOT / 'data' / 'logs'
CODE_DIR: Path = _PROJECT_ROOT / 'code'
TESTS_DIR: Path = _PROJECT_ROOT / 'tests'
DOCS_DIR: Path = _PROJECT_ROOT / 'docs'
SPECS_DIR: Path = _PROJECT_ROOT / 'specs'

def get_config() -> dict:
    """Return the current configuration as a dictionary."""
    return {
        'optical_flow_threshold': OPTICAL_FLOW_THRESHOLD,
        'embedding_dim': EMBEDDING_DIM,
        'max_memory_gb': MAX_MEMORY_GB,
        'memory_warning_threshold': MEMORY_WARNING_THRESHOLD,
        'memory_critical_threshold': MEMORY_CRITICAL_THRESHOLD,
        'validation_threshold': VALIDATION_THRESHOLD,
        'seed': SEED,
        'project_root': str(_PROJECT_ROOT),
        'data_raw_dir': str(DATA_RAW_DIR),
        'data_processed_dir': str(DATA_PROCESSED_DIR),
        'data_validation_dir': str(DATA_VALIDATION_DIR),
        'data_models_dir': str(DATA_MODELS_DIR),
        'data_results_dir': str(DATA_RESULTS_DIR),
        'data_logs_dir': str(DATA_LOGS_DIR),
        'code_dir': str(CODE_DIR),
        'tests_dir': str(TESTS_DIR),
        'docs_dir': str(DOCS_DIR),
        'specs_dir': str(SPECS_DIR),
    }

def ensure_directories() -> bool:
    """
    Ensure all required project directories exist.
    
    Creates:
    - code/, tests/, data/raw/, data/processed/, data/validation/,
      data/models/, data/results/, data/logs/, docs/, specs/
    
    Returns:
        True if all directories exist or were created successfully, False otherwise.
    """
    dirs_to_create = [
        'code', 'tests', 'docs', 'specs',
        'data/raw', 'data/processed', 'data/validation',
        'data/models', 'data/results', 'data/logs'
    ]
    
    for dir_path in dirs_to_create:
        full_path = _PROJECT_ROOT / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            return False
    
    return True