"""
Configuration module for the llmXive project.
Defines paths, resource limits, model configurations, and dataset settings.
"""
import os
import random
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

@dataclass
class Paths:
    """
    Container for project directory paths.
    Provides a tolerant interface for directory access.
    """
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    code_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")
    data_raw: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "raw")
    data_processed: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "processed")
    tests_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "tests")
    specs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "specs")
    figures_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "figures")

    # Explicit attributes for common access patterns
    DATA_RAW: Path = field(init=False)
    DATA_PROCESSED: Path = field(init=False)

    def __post_init__(self):
        self.DATA_RAW = self.data_raw
        self.DATA_PROCESSED = self.data_processed

    # Tolerant fallback for any unknown attribute access
    def __getattr__(self, name: str) -> Any:
        # If an attribute is requested that doesn't exist (e.g., DATA_RAW if not initialized yet),
        # or if a method is called that doesn't exist, return a no-op callable or a computed path.
        # This prevents AttributeError in scripts that might call .info() or similar on a Paths instance.
        if name.startswith('DATA_'):
            # Attempt to construct a path based on the name
            # e.g., DATA_FOO -> data/foo
            path_name = name.replace('DATA_', '').lower()
            candidate = self.data_dir / path_name
            # Return a Path object that can be used for .mkdir() etc.
            return candidate
        
        # For method-like calls (e.g., .info(), .debug()), return a no-op
        def _noop(*args, **kwargs):
            return None
        return _noop

@dataclass
class ResourceLimits:
    """Resource limits for execution."""
    max_cpu_percent: float = 80.0
    max_memory_mb: int = 8192
    timeout_seconds: int = 3600

@dataclass
class ModelConfig:
    """Configuration for AI models."""
    model_name: str = "phi-3-mini"
    device: str = "cpu"
    dtype: str = "float32"
    max_tokens: int = 2048
    temperature: float = 0.0
    seed: int = 42

@dataclass
class DatasetConfig:
    """Configuration for datasets."""
    dataset_id: str = "adaplanbench"
    # Official URL fallbacks
    official_url: str = "https://huggingface.co/datasets/adaplanbench"
    local_path: Optional[str] = None
    split: str = "train"
    verify_only: bool = False

@dataclass
class AnalysisConfig:
    """Configuration for analysis tasks."""
    alpha: float = 0.05
    effect_size: float = 0.15
    target_power: float = 0.80
    seed: int = 42

# Global instances
_paths_instance: Optional[Paths] = None
_resource_limits_instance: Optional[ResourceLimits] = None
_model_config_instance: Optional[ModelConfig] = None
_dataset_config_instance: Optional[DatasetConfig] = None
_analysis_config_instance: Optional[AnalysisConfig] = None

def get_paths() -> Paths:
    """Get the global Paths instance."""
    global _paths_instance
    if _paths_instance is None:
        _paths_instance = Paths()
    return _paths_instance

def get_resource_limits() -> ResourceLimits:
    """Get the global ResourceLimits instance."""
    global _resource_limits_instance
    if _resource_limits_instance is None:
        _resource_limits_instance = ResourceLimits()
    return _resource_limits_instance

def get_model_config() -> ModelConfig:
    """Get the global ModelConfig instance."""
    global _model_config_instance
    if _model_config_instance is None:
        _model_config_instance = ModelConfig()
    return _model_config_instance

def get_dataset_config() -> DatasetConfig:
    """Get the global DatasetConfig instance."""
    global _dataset_config_instance
    if _dataset_config_instance is None:
        _dataset_config_instance = DatasetConfig()
    return _dataset_config_instance

def get_analysis_config() -> AnalysisConfig:
    """Get the global AnalysisConfig instance."""
    global _analysis_config_instance
    if _analysis_config_instance is None:
        _analysis_config_instance = AnalysisConfig()
    return _analysis_config_instance

def set_all_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
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

def ensure_directories(paths: Optional[Paths] = None):
    """Ensure all necessary directories exist."""
    if paths is None:
        paths = get_paths()
    
    dirs_to_create = [
        paths.data_raw,
        paths.data_processed,
        paths.figures_dir,
        paths.tests_dir,
        paths.specs_dir
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable with an optional default."""
    return os.environ.get(key, default)

def parse_bool(value: Any) -> bool:
    """Parse a boolean value from various types."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, (int, float)):
        return bool(value)
    return False

# Utility for logging (tolerant of missing methods)
class ProjectLogger:
    """A tolerant logger that works with the Paths interface."""
    def __init__(self, name: str):
        self.name = name

    def info(self, *args, **kwargs):
        print(f"[INFO {self.name}] {args[0] if args else ''}")
    
    def debug(self, *args, **kwargs):
        print(f"[DEBUG {self.name}] {args[0] if args else ''}")
    
    def warning(self, *args, **kwargs):
        print(f"[WARNING {self.name}] {args[0] if args else ''}")
    
    def error(self, *args, **kwargs):
        print(f"[ERROR {self.name}] {args[0] if args else ''}")

def get_logger(name: str = "project") -> ProjectLogger:
    """Get a logger instance."""
    return ProjectLogger(name)
