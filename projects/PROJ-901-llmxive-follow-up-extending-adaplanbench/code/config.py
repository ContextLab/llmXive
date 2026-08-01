"""
Configuration management for the llmXive AdaPlanBench extension project.
Defines paths, random seeds, resource limits, dataset configurations,
and custom exceptions.
"""
import os
import random
import subprocess
import sys
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

# --- Custom Exceptions ---

class DatasetBlockedException(Exception):
    """Raised when the AdaPlanBench dataset is unreachable or missing required fields."""
    pass

class ResourceLimitExceeded(Exception):
    """Raised when CPU or RAM usage exceeds defined thresholds."""
    def __init__(self, message: str, resource_type: str, value: float, limit: float):
        super().__init__(message)
        self.resource_type = resource_type
        self.value = value
        self.limit = limit

# --- Data Classes ---

@dataclass
class Paths:
    """Container for all project directory paths."""
    root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_raw: Optional[Path] = None
    data_processed: Optional[Path] = None
    code: Optional[Path] = None
    tests: Optional[Path] = None
    specs: Optional[Path] = None
    figures: Optional[Path] = None

    def __post_init__(self):
        if self.data_raw is None:
            self.data_raw = self.root / "data" / "raw"
        if self.data_processed is None:
            self.data_processed = self.root / "data" / "processed"
        if self.code is None:
            self.code = self.root / "code"
        if self.tests is None:
            self.tests = self.root / "tests"
        if self.specs is None:
            self.specs = self.root / "specs"
        if self.figures is None:
            self.figures = self.root / "figures"

    # Tolerant attribute access for logger-like calls (e.g., Paths().info(...))
    def __getattr__(self, name: str):
        # If a script tries to call Paths().info(), Paths().debug(), etc., return a no-op
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'log']:
            def _noop(*args, **kwargs):
                return None
            return _noop
        raise AttributeError(f"'Paths' object has no attribute '{name}'")

    @property
    def DATA_RAW(self) -> Path:
        """Alias for data_raw to support attribute-style access."""
        return self.data_raw

    @property
    def DATA_PROCESSED(self) -> Path:
        """Alias for data_processed."""
        return self.data_processed

@dataclass
class ResourceLimits:
    """Resource constraints for execution."""
    cpu_percent_threshold: float = 90.0
    ram_gb_threshold: float = 6.5
    log_path: Path = field(default_factory=lambda: Path("data/processed/resource_logs.json"))

@dataclass
class ModelConfig:
    """Configuration for local models."""
    monolithic_model_id: str = "microsoft/Phi-3-mini-4k-instruct"
    device: str = "cpu"
    max_tokens: int = 512
    temperature: float = 0.0

@dataclass
class DatasetConfig:
    """Configuration for the AdaPlanBench dataset."""
    # Official HuggingFace dataset ID
    dataset_id: str = "llmXive/AdaPlanBench"
    # Fallback URL if HF is unreachable (hypothetical mirror or direct zip)
    fallback_url: Optional[str] = None
    # Required field to verify presence
    required_field: str = "progressive_constraints"
    # Minimum constraint count for filtering (T013)
    min_constraint_count: int = 5

@dataclass
class AnalysisConfig:
    """Configuration for statistical analysis."""
    alpha: float = 0.05
    effect_size: float = 0.15
    groups: int = 2
    seed: int = 42

# --- Global Instances ---

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

# --- Utility Functions ---

def set_all_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # If torch is available, set seeds there too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def ensure_directories(paths: Optional[Paths] = None):
    """Ensure all required directories exist."""
    if paths is None:
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
    """Get an environment variable with an optional default."""
    return os.environ.get(key, default)

def parse_bool(value: Any) -> bool:
    """Parse a string or bool to a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)

class ProjectLogger:
    """Simple logger wrapper."""
    def __init__(self, name: str = "llmXive"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def info(self, msg: str):
        self.logger.info(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def critical(self, msg: str):
        self.logger.critical(msg)

def get_logger(name: str = "llmXive") -> ProjectLogger:
    return ProjectLogger(name)

# --- Main Entry Point (for testing config) ---
if __name__ == "__main__":
    print("Loading configuration...")
    paths = get_paths()
    print(f"Root: {paths.root}")
    print(f"Data Raw: {paths.data_raw}")
    print(f"Data Processed: {paths.data_processed}")
    print(f"Dataset ID: {get_dataset_config().dataset_id}")
    print("Configuration loaded successfully.")
    ensure_directories(paths)
    print("Directories ensured.")