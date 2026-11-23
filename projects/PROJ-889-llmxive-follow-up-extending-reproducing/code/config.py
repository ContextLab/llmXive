"""
Configuration management for the llmXive pipeline.

Provides project root, path utilities, and empirical constants.
"""
import os
from pathlib import Path
from typing import Optional


# Empirical constants for ground truth validation
CORRELATION_THRESHOLD = 0.8
BASELINE_SEED = 42
BASELINE_SAMPLE_FRACTION = 0.1
DYNAMIC_THRESHOLD_MULTIPLIER = 1.5


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Assumes the project structure is:
    PROJ-889-llmxive-follow-up-extending-reproducing/
    ├── code/
    ├── data/
    ├── tests/
    └── ...
    
    Returns:
        Path to the project root.
    """
    # Try to find project root by looking for known directories
    current = Path(__file__).resolve()
    
    # Go up from code/config.py
    project_root = current.parent.parent
    
    # Verify it looks like a project root
    if not (project_root / "code").exists():
        # Fallback: try current working directory
        project_root = Path.cwd()
        
        if not (project_root / "code").exists():
            raise RuntimeError(
                "Could not determine project root. "
                "Ensure 'code/' directory exists in current path or parent directories."
            )
    
    return project_root


def ensure_paths_exist():
    """
    Ensure required directory structure exists.
    
    Creates:
    - data/raw
    - data/processed
    - code/utils
    """
    project_root = get_project_root()
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code" / "utils",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


class DataConfig:
    """Configuration for data paths and settings."""
    
    RAW_DATA_DIR = get_project_root() / "data" / "raw"
    PROCESSED_DATA_DIR = get_project_root() / "data" / "processed"
    CHERRL_LOGS_DIR = RAW_DATA_DIR / "cherrl_logs"
    
    TRAJECTORY_FILE = PROCESSED_DATA_DIR / "trajectories_divergence.csv"
    LABELED_TRAJECTORY_FILE = PROCESSED_DATA_DIR / "trajectories_labeled.csv"
    GT_TRAJECTORY_FILE = PROCESSED_DATA_DIR / "trajectories_with_gt.csv"
    METRICS_FILE = PROCESSED_DATA_DIR / "metrics.csv"


class ModelConfig:
    """Configuration for model parameters and thresholds."""
    
    WINDOW_SIZE = 20
    MIN_SAMPLES = 5
    Z_SCORE_THRESHOLD = 3.0
    CORRELATION_THRESHOLD = CORRELATION_THRESHOLD
    DYNAMIC_THRESHOLD_MULTIPLIER = DYNAMIC_THRESHOLD_MULTIPLIER


class EvalConfig:
    """Configuration for evaluation parameters."""
    
    BASELINE_SEED = BASELINE_SEED
    BASELINE_SAMPLE_FRACTION = BASELINE_SAMPLE_FRACTION
    GROUND_TRUTH_DROP_THRESHOLD = 0.1
    GROUND_TRUTH_WINDOW_SIZE = 50
    GROUND_TRUTH_SUSTAIN_STEPS = 3
    F1_STD_DEV_THRESHOLD = 0.15