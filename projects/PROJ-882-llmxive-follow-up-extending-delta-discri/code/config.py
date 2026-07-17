"""
Configuration management for the llmXive DelTA follow-up pipeline.

This module centralizes all paths, random seeds, and hyperparameters required
to run the research pipeline, ensuring reproducibility and adherence to
project constraints (e.g., N=200 examples, CPU-only execution).
"""

import os
from pathlib import Path
from typing import Dict, Any, Set

# Project Root
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Directory Structure (matches T001a)
DIR_CODE: Path = PROJECT_ROOT / "code"
DIR_DATA: Path = PROJECT_ROOT / "data"
DIR_TESTS: Path = PROJECT_ROOT / "tests"
DIR_CONTRACTS: Path = PROJECT_ROOT / "contracts"

# Data Sub-directories
DIR_DATA_RAW: Path = DIR_DATA / "raw"
DIR_DATA_PROCESSED: Path = DIR_DATA / "processed"
DIR_FIGURES: Path = DIR_DATA / "figures"

# Contracts Directory
CONTRACTS_DIR: Path = DIR_CONTRACTS

# Random Seeds (Set as requested)
# Used for reproducibility across data sampling, model initialization, etc.
SEEDS: Set[int] = {42}
DEFAULT_SEED: int = 42

# Hyperparameters
# From Plan Feasibility: N=200 examples
N_EXAMPLES: int = 200

# Oracle Configuration
# Model override from Plan: Phi-3-mini (instead of Llama-3-8B)
ORACLE_MODEL_NAME: str = "microsoft/Phi-3-mini-4k-instruct"
ORACLE_DEVICE: str = "cpu"  # CPU-only constraint
ORACLE_DTYPE: str = "float32"  # Full precision as per FR-002

# Feature Extraction Configuration
# Sentence transformer for semantic similarity (Plan override)
SENTENCE_TRANSFORMER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
SPACY_MODEL: str = "en_core_web_sm"

# Model Configuration (US2: Static Predictor)
# 2-layer MLP configuration
MLP_CONFIG: Dict[str, Any] = {
    "input_dim": 384,  # Dimension of sentence-transformers embeddings + n-gram/POS stats
    "hidden_dim": 256,
    "output_dim": 1,
    "activation": "relu",
    "dropout": 0.1,
    "num_layers": 2,  # Explicitly 2 layers as per task description
    "learning_rate": 1e-3,
    "batch_size": 32,
    "epochs": 50,
}

# Evaluation Configuration
PERMUTATION_TEST_N_SHUFFLES: int = 1000
VARIANCE_THRESHOLD: float = 1e-9  # Minimum acceptable variance for coefficients
SPEARMAN_CORRELATION_METHOD: str = "spearman"

# Execution Constraints
MAX_WALL_CLOCK_HOURS: int = 6
MAX_MEMORY_GB: int = 7

# File Paths (Conventions from tasks.md)
PATH_GSM8K_RAW: Path = DIR_DATA_RAW / "gsm8k_verified.parquet"
PATH_DELTA_COEFFICIENTS: Path = DIR_DATA_PROCESSED / "delta_coefficients.json"
PATH_STATIC_FEATURES: Path = DIR_DATA_PROCESSED / "static_features.parquet"
PATH_MLP_MODEL: Path = DIR_DATA_PROCESSED / "mlp_model.pt"
PATH_PREDICTIONS: Path = DIR_DATA_PROCESSED / "predictions.json"
PATH_EVAL_RESULTS: Path = DIR_DATA_PROCESSED / "evaluation_results.json"
PATH_ERROR_LOG: Path = DIR_DATA_PROCESSED / "error.log"

# Contract Paths
PATH_SCHEMA_DELTA: Path = CONTRACTS_DIR / "delta_oracle.schema.yaml"
PATH_SCHEMA_FEATURES: Path = CONTRACTS_DIR / "static_features.schema.yaml"
PATH_SCHEMA_PREDICTIONS: Path = CONTRACTS_DIR / "predictions.schema.yaml"

def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration for logging."""
    return {
        "n_examples": N_EXAMPLES,
        "oracle_model": ORACLE_MODEL_NAME,
        "mlp_config": MLP_CONFIG,
        "seeds": list(SEEDS),
        "paths": {
            "raw_data": str(PATH_GSM8K_RAW),
            "processed_data": str(DIR_DATA_PROCESSED),
        },
    }