"""
Configuration module for the llmXive AdaPlanBench extension project.

Defines:
  - PATHS: Absolute paths for data, code, and output directories.
  - RANDOM_SEEDS: Fixed seeds for reproducibility across numpy, torch, and random.
  - RESOURCE_LIMITS: Scaled vCPU and increased RAM limits for the execution environment.
"""

import os
import random
from pathlib import Path
from typing import Final

# ============================================================================
# Project Root & Directory Paths
# ============================================================================
# Determine project root based on the standard layout: <root>/code/config.py
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

class Paths:
    """Absolute paths for project directories."""

    ROOT: Final[Path] = _PROJECT_ROOT
    CODE: Final[Path] = ROOT / "code"
    DATA_RAW: Final[Path] = ROOT / "data" / "raw"
    DATA_PROCESSED: Final[Path] = ROOT / "data" / "processed"
    DATA_FIGURES: Final[Path] = ROOT / "data" / "figures"
    TESTS: Final[Path] = ROOT / "tests"
    SPECS: Final[Path] = ROOT / "specs"
    LOGS: Final[Path] = ROOT / "logs"

    @classmethod
    def ensure_exists(cls) -> None:
        """Create all defined directories if they do not exist."""
        for path in [
            cls.DATA_RAW,
            cls.DATA_PROCESSED,
            cls.DATA_FIGURES,
            cls.TESTS,
            cls.SPECS,
            cls.LOGS,
        ]:
            path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Random Seeds
# ============================================================================
# Fixed seed for reproducibility. Can be overridden via environment variable.
_SEED_ENV = os.getenv("LLMXIVE_RANDOM_SEED")
RANDOM_SEED: Final[int] = int(_SEED_ENV) if _SEED_ENV else 42

def set_all_seeds(seed: int = RANDOM_SEED) -> None:
    """
    Set random seeds for reproducibility across libraries.
    Must be called before any random operations or model loading.
    """
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass  # numpy might not be installed yet during early setup

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass  # torch might not be installed yet

# ============================================================================
# Resource Limits
# ============================================================================
# Scaled vCPU and increased RAM limits for the execution environment.
# These are soft limits used by the orchestration script (main.py) to fail fast.
class ResourceLimits:
    """Resource constraints for the execution environment."""

    # Scaled vCPU limit (e.g., 2 cores for parallel tasks, or 1 for strict serial)
    MAX_VCPU: Final[int] = int(os.getenv("LLMXIVE_MAX_VCPU", "2"))

    # Increased RAM limit in GB (e.g., 8GB or 16GB depending on dataset size)
    # Defaulting to 8GB as a safe baseline for SLMs and moderate datasets.
    MAX_RAM_GB: Final[int] = int(os.getenv("LLMXIVE_MAX_RAM_GB", "8"))

    # Timeout for a single task execution in seconds
    TASK_TIMEOUT_SECONDS: Final[int] = int(os.getenv("LLMXIVE_TASK_TIMEOUT", "3600"))

    # Memory usage threshold (fraction of MAX_RAM_GB) to trigger a warning
    MEMORY_WARNING_THRESHOLD: Final[float] = 0.85

    # Memory usage threshold (fraction of MAX_RAM_GB) to trigger a hard fail
    MEMORY_FAIL_THRESHOLD: Final[float] = 0.95

# ============================================================================
# Model & Agent Configuration
# ============================================================================
class ModelConfig:
    """Configuration for SLMs used in the agents."""

    # Default model for generator and monolithic baseline (CPU-tractable)
    DEFAULT_GENERATOR_MODEL: Final[str] = "microsoft/phi-2"
    DEFAULT_MONOLITHIC_MODEL: Final[str] = "microsoft/phi-2"

    # Precision for model loading (default: float32 for stability on CPU)
    DEFAULT_PRECISION: Final[str] = "float32"

    # Max tokens for generation
    MAX_NEW_TOKENS: Final[int] = 512

    # Temperature for generation (0.0 for deterministic, >0.0 for sampling)
    GENERATION_TEMPERATURE: Final[float] = 0.7

# ============================================================================
# Dataset Configuration
# ============================================================================
class DatasetConfig:
    """Configuration for the AdaPlanBench dataset."""

    # Dataset name or path. Using the official HuggingFace dataset identifier.
    DATASET_NAME: Final[str] = "adaplanbench/adaplanbench"

    # Minimum number of progressive constraints to include in the filtered set
    MIN_PROGRESSIVE_CONSTRAINTS: Final[int] = 5

    # Split to use for evaluation
    EVAL_SPLIT: Final[str] = "test"

# ============================================================================
# Analysis Configuration
# ============================================================================
class AnalysisConfig:
    """Configuration for statistical analysis."""

    # Significance level for hypothesis testing
    ALPHA: Final[float] = 0.05

    # Target power for power analysis
    TARGET_POWER: Final[float] = 0.80

    # Minimum effect size (Cohen's f²) to detect
    MIN_EFFECT_SIZE: Final[float] = 0.15

# ============================================================================
# Initialization
# ============================================================================
# Ensure directories exist upon import (safe to call multiple times)
Paths.ensure_exists()
# Set seeds immediately to ensure reproducibility from the start
set_all_seeds(RANDOM_SEED)