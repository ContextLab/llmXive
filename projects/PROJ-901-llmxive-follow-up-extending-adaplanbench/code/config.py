"""
Configuration module for the llmXive AdaPlanBench extension project.
Defines paths, resource limits, model configurations, and utility functions.
"""
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Final, Optional, Dict, Any, List
from dataclasses import dataclass, field
import numpy as np
import torch

# --- Paths Configuration ---
@dataclass
class Paths:
    """Centralized path management for the project."""
    ROOT: Path = field(init=False)
    DATA_RAW: Path = field(init=False)
    DATA_PROCESSED: Path = field(init=False)
    CODE: Path = field(init=False)
    TESTS: Path = field(init=False)
    SPECS: Path = field(init=False)
    CONTRACTS: Path = field(init=False)
    FIGURES: Path = field(init=False)

    def __post_init__(self):
        # Determine root based on where this file is located
        current_file = Path(__file__).resolve()
        self.ROOT = current_file.parent.parent
        self.DATA_RAW = self.ROOT / "data" / "raw"
        self.DATA_PROCESSED = self.ROOT / "data" / "processed"
        self.CODE = self.ROOT / "code"
        self.TESTS = self.ROOT / "tests"
        self.SPECS = self.ROOT / "specs"
        self.CONTRACTS = self.ROOT / "contracts"
        self.FIGURES = self.ROOT / "figures"

        # Ensure directories exist
        self.DATA_RAW.mkdir(parents=True, exist_ok=True)
        self.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        self.FIGURES.mkdir(parents=True, exist_ok=True)

# --- Resource Limits ---
@dataclass
class ResourceLimits:
    """Resource constraints for execution."""
    MAX_CPU_PERCENT: float = 80.0
    MAX_MEMORY_GB: float = 12.0
    TIMEOUT_SECONDS: int = 3600

# --- Model Configuration ---
@dataclass
class ModelConfig:
    """Configuration for LLM models."""
    NAME: str = "phi-3-mini"
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    PRECISION: str = "float32"  # or "float16", "bfloat16"
    DEVICE: str = "cpu"

# --- Dataset Configuration ---
@dataclass
class DatasetConfig:
    """Configuration for dataset loading and processing."""
    NAME: str = "adaplanbench/adaplanbench"
    MIN_CONSTRAINTS: int = 5
    RANDOM_SEED: int = 42

# --- Analysis Configuration ---
@dataclass
class AnalysisConfig:
    """Configuration for statistical analysis."""
    TARGET_POWER: float = 0.80
    EFFECT_SIZE_F2: float = 0.15
    SIGNIFICANCE_LEVEL: float = 0.05
    RANDOM_SEED: int = 42

# --- Global Instances ---
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
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_resource_limits() -> ResourceLimits:
    return get_resource_limits()

def get_model_config() -> ModelConfig:
    return get_model_config()

def get_dataset_config() -> DatasetConfig:
    return get_dataset_config()

def get_analysis_config() -> AnalysisConfig:
    return get_analysis_config()
