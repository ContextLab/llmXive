"""
Configuration module for llmXive project.
Defines paths, resource limits, model settings, and dataset configurations.
"""
import os
import random
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import torch

# --- Paths ---
@dataclass
class Paths:
    """Project directory structure."""
    root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_raw: Path = field(init=False)
    data_processed: Path = field(init=False)
    code: Path = field(init=False)
    tests: Path = field(init=False)
    contracts: Path = field(init=False)
    specs: Path = field(init=False)
    figures: Path = field(init=False)

    def __post_init__(self):
        self.data_raw = self.root / "data" / "raw"
        self.data_processed = self.root / "data" / "processed"
        self.code = self.root / "code"
        self.tests = self.root / "tests"
        self.contracts = self.root / "contracts"
        self.specs = self.root / "specs"
        self.figures = self.root / "figures"

        # Ensure directories exist
        ensure_directories(self)

# --- Resource Limits ---
@dataclass
class ResourceLimits:
    """Resource constraints for execution."""
    max_cpu_percent: float = 80.0
    max_memory_gb: float = 14.0
    timeout_seconds: int = 3600  # 1 hour

# --- Model Configuration ---
@dataclass
class ModelConfig:
    """Configuration for LLM agents."""
    default_model: str = "microsoft/phi-3-mini"
    max_context_length: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    device: str = "cpu"  # Default to CPU for safety, override via env
    dtype: str = "float32"

# --- Dataset Configuration ---
@dataclass
class DatasetConfig:
    """Configuration for dataset loading."""
    # AdaPlanBench official source
    dataset_name: str = "AdaPlanBench"
    # Fallback URL if HF dataset is unavailable or renamed
    fallback_url: str = "https://huggingface.co/datasets/AdaPlanBench/AdaPlanBench"
    # Local path if pre-downloaded
    local_path: Optional[str] = None
    # Filter settings
    min_progressive_constraints: int = 5
    # Streaming settings for large datasets
    streaming: bool = True

# --- Analysis Configuration ---
@dataclass
class AnalysisConfig:
    """Configuration for statistical analysis."""
    # Power analysis settings
    target_power: float = 0.80
    target_effect_size: float = 0.15  # Cohen's f²
    significance_level: float = 0.05
    # GLMM settings
    glmm_max_iter: int = 100
    glmm_tol: float = 1e-4

# --- Global Configuration Instances ---
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
        # Check environment for overrides
        device = os.getenv("LLMXIVE_DEVICE", "cpu")
        _model_config = ModelConfig(device=device)
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

def set_all_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def ensure_directories(paths: Paths):
    """Create necessary project directories."""
    directories = [
        paths.data_raw,
        paths.data_processed,
        paths.code,
        paths.tests,
        paths.contracts,
        paths.specs,
        paths.figures
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# --- Utility Functions ---
def get_env_var(name: str, default: str = "") -> str:
    """Get environment variable with a default."""
    return os.getenv(name, default)

def parse_bool(env_str: str, default: bool = False) -> bool:
    """Parse a boolean from environment string."""
    if not env_str:
        return default
    return env_str.lower() in ("true", "1", "yes", "on")
