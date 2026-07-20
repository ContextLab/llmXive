"""
Configuration module for the llmXive AdaPlanBench extension project.
Defines paths, random seeds, resource limits, and model/dataset settings.
"""
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Final, Optional, Dict, Any, List

# ============================================================================
# Project Paths
# ============================================================================
class Paths:
    """Centralized path definitions for the project."""
    # Root directory (assumes code/ is at project root)
    ROOT: Final[Path] = Path(__file__).resolve().parent.parent

    # Data directories
    RAW_DATA: Final[Path] = ROOT / "data" / "raw"
    PROCESSED_DATA: Final[Path] = ROOT / "data" / "processed"
    FIGURES: Final[Path] = ROOT / "figures"

    # Code directories
    CODE_ROOT: Final[Path] = ROOT / "code"
    DATASET_CODE: Final[Path] = CODE_ROOT / "dataset"
    AGENT_CODE: Final[Path] = CODE_ROOT / "agent"
    ANALYSIS_CODE: Final[Path] = CODE_ROOT / "analysis"

    # Test directories
    TESTS_ROOT: Final[Path] = ROOT / "tests"
    UNIT_TESTS: Final[Path] = TESTS_ROOT / "unit"
    INTEGRATION_TESTS: Final[Path] = TESTS_ROOT / "integration"
    CONTRACT_TESTS: Final[Path] = TESTS_ROOT / "contract"

    # Specs directory
    SPECS: Final[Path] = ROOT / "specs" / "001-llmxive-follow-up-extending-adaplanbench"

    # Output files
    FILTERED_TASKS: Final[Path] = PROCESSED_DATA / "filtered_tasks.csv"
    EXECUTION_TRACES: Final[Path] = PROCESSED_DATA / "execution_traces.csv"
    POWER_REPORT: Final[Path] = PROCESSED_DATA / "power_report.json"
    STATISTICAL_RESULTS: Final[Path] = PROCESSED_DATA / "statistical_results.json"
    ANNOTATION_SAMPLE: Final[Path] = PROCESSED_DATA / "annotation_sample.csv"
    HUMAN_ANNOTATIONS: Final[Path] = PROCESSED_DATA / "human_annotations.csv"
    AGREEMENT_REPORT: Final[Path] = PROCESSED_DATA / "agreement_rate_report.json"
    STATE_YAML: Final[Path] = ROOT / "state.yaml"

    # Ensure directories exist on import (optional, can be moved to init script)
    @classmethod
    def ensure_dirs(cls) -> None:
        """Create all defined directories if they do not exist."""
        dirs = [
            cls.RAW_DATA, cls.PROCESSED_DATA, cls.FIGURES,
            cls.DATASET_CODE, cls.AGENT_CODE, cls.ANALYSIS_CODE,
            cls.UNIT_TESTS, cls.INTEGRATION_TESTS, cls.CONTRACT_TESTS
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Random Seeds
# ============================================================================
DEFAULT_SEED: Final[int] = 42

def set_all_seeds(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch.
    Must be called before any random operations.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

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
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


# ============================================================================
# Resource Limits
# ============================================================================
class ResourceLimits:
    """
    Configuration for resource constraints to prevent runaway processes.
    Scaled vCPU and increased RAM limits as per project requirements.
    """
    # CPU limits (in seconds of CPU time)
    # Scaled down from default to enforce efficient code, but increased slightly
    # from a very strict default to allow for model loading.
    # Default soft limit on many systems is 'unlimited' or very high.
    # We set a hard cap to fail fast.
    CPU_TIME_LIMIT_SECONDS: Final[int] = 3600  # 1 hour of CPU time

    # Memory limits (in bytes)
    # Increased RAM limit: 12GB (12 * 1024^3)
    # This is sufficient for loading small models (Phi-2, etc.) and datasets
    # without OOM on standard CI runners, but strict enough to catch leaks.
    MEMORY_LIMIT_BYTES: Final[int] = 12 * 1024 * 1024 * 1024

    # Wall-clock time limit (seconds)
    # Separate from CPU time to handle I/O waits or multi-threaded stalls.
    WALL_CLOCK_LIMIT_SECONDS: Final[int] = 7200  # 2 hours

    @classmethod
    def apply(cls) -> None:
        """
        Apply resource limits to the current process using the resource module.
        Only works on Unix-like systems.
        """
        if sys.platform == "win32":
            # Windows does not support resource module limits in the same way.
            # We log a warning but do not fail, as the main.py wrapper
            # might handle monitoring differently or this might be a dev environment.
            import warnings
            warnings.warn(
                "ResourceLimits.apply() not supported on Windows. "
                "Limits will be enforced by external process monitor if available."
            )
            return

        import resource

        # Set CPU time limit
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cls.CPU_TIME_LIMIT_SECONDS, cls.CPU_TIME_LIMIT_SECONDS))
        except (ValueError, resource.error) as e:
            # If the limit cannot be set (e.g., insufficient privileges), log and continue
            # The main.py wrapper should catch the SIGXCPU if it happens later.
            import warnings
            warnings.warn(f"Failed to set CPU limit: {e}")

        # Set Memory limit (RLIMIT_AS)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (cls.MEMORY_LIMIT_BYTES, cls.MEMORY_LIMIT_BYTES))
        except (ValueError, resource.error) as e:
            import warnings
            warnings.warn(f"Failed to set memory limit: {e}")

        # Set Wall clock limit (RLIMIT_CPU is CPU time, RLIMIT_RTTIME is real time on some systems,
        # but standard resource module doesn't expose RLIMIT_RTTIME directly in a portable way for limits).
        # We rely on the main.py wrapper for wall-clock enforcement via time.time() checks.


# ============================================================================
# Model Configuration
# ============================================================================
@dataclass
class ModelConfig:
    """Configuration for model loading and execution."""
    # Default model for CPU-tractable experiments
    DEFAULT_MODEL_NAME: Final[str] = "microsoft/phi-2"
    MAX_SEQ_LENGTH: Final[int] = 2048
    DEVICE: Final[str] = "cpu"  # Force CPU for reproducibility in CI unless overridden
    TORCH_DTYPE: Final[str] = "float32"  # Default precision

    # Generator temperature (0 for deterministic)
    GENERATOR_TEMPERATURE: Final[float] = 0.0

    # Constraints for resolution
    RESOLUTION_TIMEOUT_SECONDS: Final[int] = 10


# ============================================================================
# Dataset Configuration
# ============================================================================
@dataclass
class DatasetConfig:
    """Configuration for dataset loading and filtering."""
    # AdaPlanBench dataset identifier
    DATASET_NAME: Final[str] = "adaplanbench/adaplanbench"
    
    # Minimum number of progressive constraints to include
    MIN_CONSTRAINTS: Final[int] = 5
    
    # Random seed for sampling
    SAMPLING_SEED: Final[int] = DEFAULT_SEED
    
    # Streaming flag for large datasets
    STREAMING: Final[bool] = True
    
    # Number of samples to process if full dataset is too large (fallback)
    MAX_SAMPLES: Optional[int] = 1000  # Set to None for full dataset


# ============================================================================
# Analysis Configuration
# ============================================================================
@dataclass
class AnalysisConfig:
    """Configuration for statistical analysis."""
    # GLMM parameters
    GLMM_MAX_ITERATIONS: Final[int] = 1000
    GLMM_TOL: Final[float] = 1e-5
    
    # Power analysis target
    POWER_TARGET: Final[float] = 0.80
    EFFECT_SIZE_F2: Final[float] = 0.15  # Medium effect size
    
    # Significance level
    ALPHA: Final[float] = 0.05


# Import here to avoid circular dependency if dataclasses used earlier
from dataclasses import dataclass, field

# Initialize paths on module load
Paths.ensure_dirs()
set_all_seeds(DEFAULT_SEED)