import os
import random
import subprocess
import sys
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

# --- Custom Exceptions ---

class DatasetBlockedException(Exception):
    """Raised when the dataset is blocked or unavailable."""
    pass

class ResourceLimitExceeded(Exception):
    """Raised when CPU or RAM usage exceeds configured limits."""
    pass

class PowerInsufficientError(Exception):
    """Raised when statistical power is insufficient for the analysis."""
    pass

# --- Configuration Dataclasses ---

@dataclass
class ResourceLimits:
    MAX_CPU_PERCENT: float = 90.0
    MAX_RAM_GB: float = 6.5

@dataclass
class ModelConfig:
    MODEL_NAME: str = "microsoft/phi-3-mini"
    MAX_LENGTH: int = 2048
    TEMPERATURE: float = 0.7
    DEVICE: str = "cpu" # Default to CPU for safety in restricted envs

@dataclass
class DatasetConfig:
    DATASET_ID: str = "llmXive/adaplanbench" # Placeholder ID
    OFFICIAL_URL: str = "https://huggingface.co/datasets/llmXive/adaplanbench"
    FILTER_MIN_CONSTRAINTS: int = 5

@dataclass
class AnalysisConfig:
    ALPHA: float = 0.05
    EFFECT_SIZE: float = 0.15
    POWER_THRESHOLD: float = 0.80

# --- Paths Class ---

class Paths:
    """
    Manages project paths.
    Provides attributes like RAW, PROCESSED, CODE, etc.
    """
    def __init__(self, root: Optional[Path] = None):
        if root is None:
            # Assume current working directory is project root
            root = Path.cwd()
        self.ROOT = root
        self.DATA = self.ROOT / "data"
        self.DATA_RAW = self.DATA / "raw"
        self.DATA_PROCESSED = self.DATA / "processed"
        self.CODE = self.ROOT / "code"
        self.SPECS = self.ROOT / "specs"
        self.TESTS = self.ROOT / "tests"
        self.FIGURES = self.DATA / "figures"

    # Logger-style methods for tolerance
    def info(self, *args, **kwargs):
        logging.info(*args, **kwargs)
    
    def debug(self, *args, **kwargs):
        logging.debug(*args, **kwargs)
    
    def warning(self, *args, **kwargs):
        logging.warning(*args, **kwargs)
    
    def error(self, *args, **kwargs):
        logging.error(*args, **kwargs)

# --- Global State ---

_paths_instance: Optional[Paths] = None
_resource_limits_instance: Optional[ResourceLimits] = None
_model_config_instance: Optional[ModelConfig] = None
_dataset_config_instance: Optional[DatasetConfig] = None
_analysis_config_instance: Optional[AnalysisConfig] = None

# --- Getters ---

def get_paths() -> Paths:
    global _paths_instance
    if _paths_instance is None:
        _paths_instance = Paths()
    return _paths_instance

def get_resource_limits() -> ResourceLimits:
    global _resource_limits_instance
    if _resource_limits_instance is None:
        _resource_limits_instance = ResourceLimits()
    return _resource_limits_instance

def get_model_config() -> ModelConfig:
    global _model_config_instance
    if _model_config_instance is None:
        _model_config_instance = ModelConfig()
    return _model_config_instance

def get_dataset_config() -> DatasetConfig:
    global _dataset_config_instance
    if _dataset_config_instance is None:
        _dataset_config_instance = DatasetConfig()
    return _dataset_config_instance

def get_analysis_config() -> AnalysisConfig:
    global _analysis_config_instance
    if _analysis_config_instance is None:
        _analysis_config_instance = AnalysisConfig()
    return _analysis_config_instance

# --- Utility Functions ---

def set_all_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # If torch is available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def ensure_directories():
    """Ensure all required directories exist."""
    paths = get_paths()
    dirs = [
        paths.DATA_RAW,
        paths.DATA_PROCESSED,
        paths.CODE,
        paths.SPECS,
        paths.TESTS,
        paths.FIGURES
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable."""
    return os.environ.get(key, default)

def parse_bool(value: Any) -> bool:
    """Parse a boolean from string or bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)

class ProjectLogger:
    """Simple logger wrapper."""
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, msg):
        self.logger.info(msg)
    
    def error(self, msg):
        self.logger.error(msg)
    
    def warning(self, msg):
        self.logger.warning(msg)

def get_logger(name: str = "llmXive") -> ProjectLogger:
    return ProjectLogger(name)
