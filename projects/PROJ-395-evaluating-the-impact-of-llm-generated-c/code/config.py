"""
Configuration module for the LLM memory impact evaluation project.

This module defines all project-wide constants and parameters including:
- Random seeds for reproducibility
- Model parameters and timeouts
- Memory limits for CI environments
- Dataset paths and versioning

Usage:
    import config
    timeout = config.TIMEOUT_SECONDS
    seed = config.RANDOM_SEED
"""

import os
from typing import Final

# ============================================================================
# Random Seeds
# ============================================================================
RANDOM_SEED: Final[int] = 42
"""Seed for numpy, random, and torch to ensure reproducibility."""

# ============================================================================
# Model Parameters
# ============================================================================
MODEL_NAME: Final[str] = 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
"""Primary model for CPU-tractable generation."""

MODEL_MAX_LENGTH: Final[int] = 2048
"""Maximum sequence length for model generation."""

GENERATION_TEMPERATURE: Final[float] = 0.7
"""Sampling temperature for code generation."""

GENERATION_MAX_NEW_TOKENS: Final[int] = 512
"""Maximum new tokens to generate per solution."""

# ============================================================================
# Execution Limits
# ============================================================================
TIMEOUT_SECONDS: Final[int] = 60
"""Timeout for code execution (seconds). Per spec A-012."""

CI_MEMORY_LIMIT_GB: Final[float] = 7.0
"""Memory limit for CI runners (GB). Used for censored data handling."""

MAX_RETRIES: Final[int] = 2
"""Maximum retry attempts for transient failures."""

# ============================================================================
# Statistical Analysis Parameters
# ============================================================================
STABILITY_IQR_THRESHOLD: Final[float] = 0.15
"""IQR threshold for stability check (15% of median)."""

STABILITY_MAX_RUNS: Final[int] = 3
"""Number of runs for stability assessment."""

SIGNIFICANCE_LEVEL: Final[float] = 0.05
"""Alpha level for statistical significance testing."""

# ============================================================================
# Dataset Configuration
# ============================================================================
DATASET_SOURCE: Final[str] = 'mbpp'
"""Dataset source: 'human_eval' or 'mbpp'."""

DATASET_SPLIT: Final[str] = 'test'
"""Dataset split to use for evaluation."""

SAMPLE_SIZE: Final[int] = 30
"""Number of problems to sample for evaluation."""

# ============================================================================
# File Paths
# ============================================================================
PROJECT_ROOT: Final[str] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""Root directory of the project."""

DATA_RAW_DIR: Final[str] = os.path.join(PROJECT_ROOT, 'data', 'raw')
"""Directory for raw downloaded datasets."""

DATA_PROCESSED_DIR: Final[str] = os.path.join(PROJECT_ROOT, 'data', 'processed')
"""Directory for processed data files."""

STATE_DIR: Final[str] = os.path.join(PROJECT_ROOT, 'state')
"""Directory for state snapshots and versioning."""

CODE_DIR: Final[str] = os.path.join(PROJECT_ROOT, 'code')
"""Directory for source code modules."""

# ============================================================================
# Manifest and Versioning
# ============================================================================
DATASET_MANIFEST_PATH: Final[str] = os.path.join(DATA_RAW_DIR, 'dataset_manifest.yaml')
"""Path to the dataset version manifest."""

PROFILING_ENV_PATH: Final[str] = os.path.join(CODE_DIR, 'profiling_env.yaml')
"""Path to the profiling environment configuration."""

MEMORY_MEASUREMENTS_PATH: Final[str] = os.path.join(
    DATA_PROCESSED_DIR, 'memory_measurements.csv'
)
"""Path to the memory measurements CSV output."""

ANALYSIS_REPORT_PATH: Final[str] = os.path.join(
    DATA_PROCESSED_DIR, 'analysis_report.json'
)
"""Path to the statistical analysis report output."""