"""
Environment Configuration and Path Management.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from code.config import PROJECT_ROOT, get_project_path

logger = logging.getLogger(__name__)

class EnvironmentConfig:
    def __init__(self):
        self.project_root = get_project_path()
        self.data_dir = self.project_root / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.figures_dir = self.project_root / "figures"
        self.logs_dir = self.project_root / "logs"
        self.tests_dir = self.project_root / "tests"
        self.contracts_dir = self.project_root / "contracts"
        self.code_dir = self.project_root / "code"
        
        # Defaults
        self.random_seed = 42
        self.max_workers = 2
        self.timeout_seconds = 3600
        self.batch_size = 1000
        self.permutation_count = 5000
        self.alpha_thresholds = [0.01, 0.05, 0.1]

_config: Optional[EnvironmentConfig] = None

def get_config() -> EnvironmentConfig:
    global _config
    if _config is None:
        _config = EnvironmentConfig()
        ensure_directories()
    return _config

def get_debug() -> bool:
    return os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

def get_log_level() -> int:
    level = os.getenv("LOG_LEVEL", "INFO")
    return getattr(logging, level.upper(), logging.INFO)

def get_random_seed() -> int:
    return get_config().random_seed

def get_data_dir() -> Path:
    return get_config().data_dir

def get_raw_dir() -> Path:
    return get_config().raw_dir

def get_processed_dir() -> Path:
    return get_config().processed_dir

def get_output_dir() -> Path:
    return get_config().processed_dir

def get_figures_dir() -> Path:
    return get_config().figures_dir

def get_max_workers() -> int:
    return get_config().max_workers

def get_timeout_seconds() -> int:
    return get_config().timeout_seconds

def get_batch_size() -> int:
    return get_config().batch_size

def get_permutation_count() -> int:
    return get_config().permutation_count

def get_alpha_thresholds() -> List[float]:
    return get_config().alpha_thresholds

def ensure_directories():
    """Ensure all required directories exist."""
    config = get_config()
    dirs = [
        config.data_dir, config.raw_dir, config.processed_dir,
        config.figures_dir, config.logs_dir, config.tests_dir,
        config.contracts_dir, config.code_dir
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")
