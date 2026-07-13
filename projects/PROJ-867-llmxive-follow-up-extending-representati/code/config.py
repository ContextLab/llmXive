"""
Configuration module for llmXive Representation Forcing pipeline.

This module centralizes all hyperparameters, file paths, and random seeds
required for reproducibility and experiment management.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# Project Root and Directory Structure
# ============================================================================

# Root of the project repository
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Standardized subdirectories
CODE_DIR: Path = PROJECT_ROOT / "code"
DATA_DIR: Path = PROJECT_ROOT / "data"
TESTS_DIR: Path = PROJECT_ROOT / "tests"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
FIGURES_DIR: Path = DATA_DIR / "figures"
RESULTS_DIR: Path = DATA_DIR / "results"
LOGS_DIR: Path = DATA_DIR / "logs"

# Ensure directories exist (created at runtime or by setup)
def ensure_dirs() -> None:
    """Create all standard project directories if they do not exist."""
    for directory in [DATA_DIR, FIGURES_DIR, RESULTS_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Random Seeds (Reproducibility)
# ============================================================================

# Global random seed for numpy, torch, and python
RANDOM_SEED: int = 42

# Specific seeds for data splits if needed
SPLIT_SEED: int = 42

# ============================================================================
# Hyperparameters: Data Loading & Preprocessing
# ============================================================================

# Target image resolution (width, height)
IMAGE_SIZE: int = 224

# Batch size for data loading (CPU-optimized to stay within 4GB RAM)
BATCH_SIZE: int = 8

# Number of workers for data loading (0 for CPU-only safety on limited runners)
NUM_WORKERS: int = 0

# Maximum number of tokens per sequence (context window)
MAX_CONTEXT_LENGTH: int = 512

# ============================================================================
# Hyperparameters: Model Architecture (RF Encoder)
# ============================================================================

# Pretrained model name for LayoutLMv3
RF_MODEL_NAME: str = "microsoft/layoutlmv3-base"

# Whether to freeze the encoder weights
FREEZE_ENCODER: bool = True

# Whether to disable pixel-decoding layers
DISABLE_PIXEL_DECODER: bool = True

# ============================================================================
# Hyperparameters: Training (Autoregressive Model)
# ============================================================================

# Maximum number of epochs (Constitution VII override: hard limit 2)
MAX_EPOCHS: int = 2

# Learning rate for the autoregressive model
LEARNING_RATE: float = 1e-4

# Weight decay for regularization
WEIGHT_DECAY: float = 0.01

# Dropout probability
DROPOUT: float = 0.1

# Number of transformer layers in the autoregressive model (~30M params target)
NUM_LAYERS: int = 6

# Hidden dimension size
HIDDEN_SIZE: int = 512

# Number of attention heads
NUM_HEADS: int = 8

# ============================================================================
# Hyperparameters: Evaluation & Statistics
# ============================================================================

# Significance level for statistical tests (alpha)
ALPHA: float = 0.05

# Minimum syntactic validity rate to consider a model "successful"
MIN_VALIDITY_RATE: float = 0.80

# ============================================================================
# Resource Constraints (FR-007: 4GB Memory Limit)
# ============================================================================

# Maximum allowed memory in GB
MAX_MEMORY_GB: float = 4.0

# Timeout for CI job in seconds (6 hours)
CI_TIMEOUT_SECONDS: int = 6 * 60 * 60

# ============================================================================
# Dataset Paths & URLs
# ============================================================================

# HuggingFace dataset identifier for PubLayNet
PUBLAYNET_DATASET_ID: str = "facebook/publaynet"

# Local cache directory for downloaded datasets
DATASET_CACHE_DIR: Path = DATA_DIR / "datasets"

# ============================================================================
# Output File Paths
# ============================================================================

# Path for training logs
TRAINING_LOG_PATH: Path = RESULTS_DIR / "training_log.json"

# Path for aggregated scores
AGGREGATED_SCORES_PATH: Path = RESULTS_DIR / "aggregated_scores.json"

# Path for runtime metrics
METRICS_PATH: Path = RESULTS_DIR / "metrics.json"

# Path for complexity metrics
COMPLEXITY_METRICS_PATH: Path = RESULTS_DIR / "complexity_metrics.json"

# ============================================================================
# Configuration Dictionary for Export
# ============================================================================

def get_config_dict() -> Dict[str, Any]:
    """Return a dictionary of all configuration parameters."""
    return {
        "project_root": str(PROJECT_ROOT),
        "random_seed": RANDOM_SEED,
        "image_size": IMAGE_SIZE,
        "batch_size": BATCH_SIZE,
        "max_context_length": MAX_CONTEXT_LENGTH,
        "rf_model_name": RF_MODEL_NAME,
        "freeze_encoder": FREEZE_ENCODER,
        "max_epochs": MAX_EPOCHS,
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "dropout": DROPOUT,
        "num_layers": NUM_LAYERS,
        "hidden_size": HIDDEN_SIZE,
        "num_heads": NUM_HEADS,
        "alpha": ALPHA,
        "max_memory_gb": MAX_MEMORY_GB,
        "ci_timeout_seconds": CI_TIMEOUT_SECONDS,
        "publaynet_dataset_id": PUBLAYNET_DATASET_ID,
    }