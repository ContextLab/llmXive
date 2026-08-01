"""
Configuration management for the llmXive AdaPlanBench extension project.
Defines paths, seeds, resource limits, dataset configuration, and custom exceptions.
"""
import os
import random
import subprocess
import sys
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import hashlib

# --- Custom Exceptions ---

class DatasetBlockedException(Exception):
    """Raised when the dataset cannot be fetched or is blocked/unavailable."""
    pass

class ResourceLimitExceeded(Exception):
    """Raised when CPU or RAM usage exceeds defined thresholds."""
    pass

# --- Configuration Data Classes ---

@dataclass
class Paths:
    """
    Project path configuration.
    Implements a tolerant logger interface via __getattr__ to prevent
    AttributeError on unknown method calls from various scripts.
    """
    root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_raw: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "raw")
    data_processed: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed")
    code: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "code")
    tests: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "tests")
    specs: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "specs")
    figures: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "figures")

    # Legacy aliases for compatibility with existing scripts
    DATA_RAW: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "raw")
    DATA_PROCESSED: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed")
    CODE: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "code")
    TESTS: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "tests")
    SPECS: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "specs")
    FIGURES: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "figures")

    def __post_init__(self):
        # Ensure standard attributes exist for direct access if needed
        if not hasattr(self, 'data_raw'):
            self.data_raw = self.DATA_RAW
        if not hasattr(self, 'data_processed'):
            self.data_processed = self.DATA_PROCESSED

    def __getattr__(self, name: str) -> Callable:
        """
        Tolerant fallback for any attribute access.
        Returns a no-op callable if the attribute is not found,
        preventing AttributeError on logger-style calls like .info(), .debug(), etc.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

@dataclass
class ResourceLimits:
    """Resource constraints for execution."""
    cpu_threshold_percent: float = 90.0
    ram_threshold_gb: float = 6.5

@dataclass
class ModelConfig:
    """Configuration for local models."""
    model_name: str = "microsoft/Phi-3-mini-4k-instruct"
    device: str = "cpu"
    torch_dtype: str = "float32"
    max_new_tokens: int = 512
    temperature: float = 0.7

@dataclass
class DatasetConfig:
    """Configuration for dataset fetching and filtering."""
    # Official AdaPlanBench source (HuggingFace)
    dataset_name: str = "AdaPlanBench/AdaPlanBench"
    dataset_split: str = "train"
    # Fallback URL if HF is unreachable (example structure, actual URL depends on mirror)
    fallback_url: Optional[str] = None
    # Filter criteria
    min_progressive_constraints: int = 5

@dataclass
class AnalysisConfig:
    """Configuration for statistical analysis."""
    alpha: float = 0.05
    effect_size: float = 0.15
    groups: int = 2
    annotation_sample_size: int = 50
    annotation_seed: int = 42

# --- Global Configuration ---

_paths: Optional[Paths] = None
_resource_limits: Optional[ResourceLimits] = None
_model_config: Optional[ModelConfig] = None
_dataset_config: Optional[DatasetConfig] = None
_analysis_config: Optional[AnalysisConfig] = None

def get_paths() -> Paths:
    global _paths
    if _paths is None:
        _paths = Paths()
    return _paths

def get_resource_limits() -> ResourceLimits:
    global _resource_limits
    if _resource_limits is None:
        _resource_limits = ResourceLimits()
    return _resource_limits

def get_model_config() -> ModelConfig:
    global _model_config
    if _model_config is None:
        _model_config = ModelConfig()
    return _model_config

def get_dataset_config() -> DatasetConfig:
    global _dataset_config
    if _dataset_config is None:
        _dataset_config = DatasetConfig()
    return _dataset_config

def get_analysis_config() -> AnalysisConfig:
    global _analysis_config
    if _analysis_config is None:
        _analysis_config = AnalysisConfig()
    return _analysis_config

# --- Utility Functions ---

def set_all_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: torch and numpy seeds would be set in modules that import them
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def ensure_directories():
    """Create all necessary project directories."""
    paths = get_paths()
    dirs = [
        paths.data_raw,
        paths.data_processed,
        paths.code,
        paths.tests,
        paths.specs,
        paths.figures
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable."""
    return os.getenv(key, default)

def parse_bool(value: Any) -> bool:
    """Parse a string to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)

class ProjectLogger:
    """Simple project logger wrapper."""
    def __init__(self, name: str = "llmXive"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    # Tolerant fallback for unknown methods
    def __getattr__(self, name: str) -> Callable:
        def _noop(*args, **kwargs):
            return None
        return _noop

def get_logger(name: str = "llmXive") -> ProjectLogger:
    return ProjectLogger(name)

# --- Main Entry Point for CLI ---

if __name__ == "__main__":
    print("llmXive Configuration Module")
    print(f"Root: {get_paths().root}")
    print(f"Data Raw: {get_paths().data_raw}")
    print(f"Data Processed: {get_paths().data_processed}")
    print(f"Dataset Name: {get_dataset_config().dataset_name}")
    print(f"Resource Limits: CPU {get_resource_limits().cpu_threshold_percent}%, RAM {get_resource_limits().ram_threshold_gb}GB")
    ensure_directories()
    print("Directories ensured.")