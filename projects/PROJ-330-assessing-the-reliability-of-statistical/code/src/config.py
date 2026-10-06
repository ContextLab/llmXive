"""
Configuration management for the genomic analysis pipeline.

This module defines all configuration constants, paths, and runtime thresholds
used throughout the project.
"""
import os
from pathlib import Path
from typing import Final

# Project root directory
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.parent

# State file for tracking artifacts
STATE_FILE: Final[Path] = PROJECT_ROOT / "state.yaml"

# Memory limits (in MB) - Task T033: Ensure <6GB usage
MEMORY_LIMIT_MB: Final[int] = 6000
MEMORY_WARNING_THRESHOLD_MB: Final[int] = 5000

# Runtime thresholds
MAX_RUNTIME_SECONDS: Final[int] = 6 * 3600  # 6 hours
MIN_PERMUTATIONS: Final[int] = 100

# Data paths
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
ARTIFACTS_DIR: Final[Path] = PROJECT_ROOT / "artifacts"
FIGURES_DIR: Final[Path] = PROJECT_ROOT / "figures"
CACHE_DIR: Final[Path] = PROJECT_ROOT / "cache"

# Random seeds for reproducibility
RANDOM_SEED: Final[int] = 42
NUMPY_SEED: Final[int] = 42

# Gene filtering thresholds
MIN_GENE_COUNT: Final[int] = 5
MIN_SAMPLES_PER_BATCH: Final[int] = 20

# Statistical thresholds
PVALUE_THRESHOLD: Final[float] = 0.05
KS_TEST_THRESHOLD: Final[float] = 0.05

# Chunk sizes for streaming
DEFAULT_CHUNK_SIZE: Final[int] = 10000

def ensure_directories():
    """
    Create all required directories if they don't exist.
    
    This function ensures that the project has the necessary directory structure
    for data, artifacts, figures, and cache.
    """
    directories = [
        DATA_DIR,
        ARTIFACTS_DIR,
        FIGURES_DIR,
        CACHE_DIR,
        PROJECT_ROOT / "code" / "src",
        PROJECT_ROOT / "code" / "scripts",
        PROJECT_ROOT / "code" / "tests"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_memory_limit_mb() -> int:
    """
    Get the memory limit in megabytes.
    
    Returns:
        int: Memory limit in MB.
    """
    return MEMORY_LIMIT_MB

def get_memory_warning_threshold_mb() -> int:
    """
    Get the memory warning threshold in megabytes.
    
    Returns:
        int: Warning threshold in MB.
    """
    return MEMORY_WARNING_THRESHOLD_MB