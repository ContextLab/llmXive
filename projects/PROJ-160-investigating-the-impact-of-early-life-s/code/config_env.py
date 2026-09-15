"""
Environment configuration management for the llmXive pipeline.

This module provides centralized access to environment variables,
with sensible defaults derived from the project structure.
It supports .env file loading via python-dotenv if available.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

# Attempt to import dotenv; if missing, environment variables must be set in shell
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = lambda: None  # type: ignore

from code.config import PROJECT_ROOT, get_project_path

class EnvironmentConfig:
    """Container for environment configuration values."""
    
    def __init__(self):
        self.project_root: Path = PROJECT_ROOT
        self.data_raw_dir: Path = self.project_root / "data" / "raw"
        self.data_processed_dir: Path = self.project_root / "data" / "processed"
        self.data_figures_dir: Path = self.project_root / "figures"
        self.code_dir: Path = self.project_root / "code"
        self.tests_dir: Path = self.project_root / "tests"
        self.contracts_dir: Path = self.project_root / "contracts"
        self.logs_dir: Path = self.project_root / "logs"
        
        # Runtime settings
        self.random_seed: int = 42
        self.log_level: int = logging.INFO
        self.debug: bool = False
        self.max_workers: int = 2
        self.timeout_seconds: int = 21600  # 6 hours
        self.batch_size: int = 100
        self.permutation_count: int = 5000
        self.alpha_thresholds: List[float] = [0.01, 0.05, 0.1]
        
        # Load environment variables
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Project root override
        if os.getenv("PROJECT_ROOT"):
            self.project_root = Path(os.getenv("PROJECT_ROOT"))
        
        # Directory overrides
        if os.getenv("DATA_RAW_DIR"):
            self.data_raw_dir = Path(os.getenv("DATA_RAW_DIR"))
        if os.getenv("DATA_PROCESSED_DIR"):
            self.data_processed_dir = Path(os.getenv("DATA_PROCESSED_DIR"))
        if os.getenv("DATA_FIGURES_DIR"):
            self.data_figures_dir = Path(os.getenv("DATA_FIGURES_DIR"))
        
        # Runtime settings
        if os.getenv("RANDOM_SEED"):
            try:
                self.random_seed = int(os.getenv("RANDOM_SEED"))
            except ValueError:
                pass
        
        if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
            self.debug = True
            self.log_level = logging.DEBUG
        
        log_level_str = os.getenv("LOG_LEVEL", "INFO")
        if hasattr(logging, log_level_str.upper()):
            self.log_level = getattr(logging, log_level_str.upper())
        
        if os.getenv("MAX_WORKERS"):
            try:
                self.max_workers = int(os.getenv("MAX_WORKERS"))
            except ValueError:
                pass
        
        if os.getenv("TIMEOUT_SECONDS"):
            try:
                self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS"))
            except ValueError:
                pass
        
        if os.getenv("BATCH_SIZE"):
            try:
                self.batch_size = int(os.getenv("BATCH_SIZE"))
            except ValueError:
                pass
        
        if os.getenv("PERMUTATION_COUNT"):
            try:
                self.permutation_count = int(os.getenv("PERMUTATION_COUNT"))
            except ValueError:
                pass
        
        if os.getenv("ALPHA_THRESHOLDS"):
            try:
                self.alpha_thresholds = [float(x) for x in os.getenv("ALPHA_THRESHOLDS").split(",")]
            except ValueError:
                pass

    def ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        for dir_path in [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_figures_dir,
            self.logs_dir,
            self.tests_dir,
            self.contracts_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

# Global configuration instance
_config: Optional[EnvironmentConfig] = None

def get_config() -> EnvironmentConfig:
    """Get the global environment configuration instance."""
    global _config
    if _config is None:
        _config = EnvironmentConfig()
    return _config

def get_debug() -> bool:
    """Check if debug mode is enabled."""
    return get_config().debug

def get_log_level() -> int:
    """Get the configured log level."""
    return get_config().log_level

def get_random_seed() -> int:
    """Get the configured random seed."""
    return get_config().random_seed

def get_data_dir() -> Path:
    """Get the base data directory."""
    return get_config().project_root / "data"

def get_raw_dir() -> Path:
    """Get the raw data directory."""
    return get_config().data_raw_dir

def get_processed_dir() -> Path:
    """Get the processed data directory."""
    return get_config().data_processed_dir

def get_output_dir() -> Path:
    """Alias for processed directory."""
    return get_processed_dir()

def get_figures_dir() -> Path:
    """Get the figures directory."""
    return get_config().data_figures_dir

def get_max_workers() -> int:
    """Get the configured maximum number of workers."""
    return get_config().max_workers

def get_timeout_seconds() -> int:
    """Get the configured timeout in seconds."""
    return get_config().timeout_seconds

def get_batch_size() -> int:
    """Get the configured batch size."""
    return get_config().batch_size

def get_permutation_count() -> int:
    """Get the configured permutation count."""
    return get_config().permutation_count

def get_alpha_thresholds() -> List[float]:
    """Get the configured alpha thresholds."""
    return get_config().alpha_thresholds

def ensure_directories() -> None:
    """Ensure all configured directories exist."""
    get_config().ensure_directories()
