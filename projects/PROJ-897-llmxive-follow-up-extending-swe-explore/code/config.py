"""
Configuration module for llmXive.
Defines paths, random seeds, model config, and critical thresholds.
Updated to align with Spec FR-001 (Coverage-based Hard Selection) and SC-003 (Wilcoxon/Permutation).
"""
import os
from pathlib import Path
from typing import Final, Dict, Any, List
from datetime import datetime

# Project Root
_PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent

# Paths
DATA_RAW: Final = _PROJECT_ROOT / "data" / "raw"
DATA_CURATED: Final = _PROJECT_ROOT / "data" / "curated"
DATA_RESULTS: Final = _PROJECT_ROOT / "data" / "results"
DATA_FIGURES: Final = _PROJECT_ROOT / "figures"
CODE_DIR: Final = _PROJECT_ROOT / "code"
SPECS_DIR: Final = _PROJECT_ROOT / "specs"
STATE_DIR: Final = _PROJECT_ROOT / "state"

# Random Seeds
RANDOM_SEED: Final = 42
SWEEP_SEED: Final = 42

# Model Config (CPU-only, 8-bit quantization default)
MODEL_USE_GPU: Final = False
MODEL_QUANTIZATION_BITS: Final = 8
MODEL_N_GPU_LAYERS: Final = 0
MODEL_MAX_CONTEXT: Final = 4096

# Critical Thresholds
# Spec FR-001: Hard instance selection based on initial coverage scores
COMPLEXITY_THRESHOLD: Final = 50  # Diagnostic only, not used for selection
HARD_INSTANCE_PERCENTILE: Final = 0.20
MIN_SYNTHETIC_ISSUES: Final = 10
VALIDATION_SAMPLE_SIZE: Final = 5
COVERAGE_COLUMN_NAME: Final = 'initial_coverage'

# Spec SC-003: Statistical routing is now deterministic based on tie presence
# TIE_THRESHOLD removed; routing logic checks for any ties (count > 0)

# Turn limits for sweep analysis
TURN_LIMITS: Final = [1, 2, 3, 4]

# Sweep configuration
SWEEP_SAMPLE_SIZE: Final = 100  # Representative sample size for turn-limit sweeps

# Execution Constraints
MAX_EXECUTION_HOURS: Final = 6.0
RAM_LIMIT_GB: Final = 7.0

# Dataset Source
# Using SWE-bench Lite as the verified source for SWE-Explore benchmark data
HF_DATASET_NAME: Final = "princeton-nlp/SWE-bench_Lite"
HF_DATASET_SPLIT: Final = "test"

def get_path(key: str) -> Path:
    """Get a path by key name."""
    mapping = {
        "raw": DATA_RAW,
        "curated": DATA_CURATED,
        "results": DATA_RESULTS,
        "figures": DATA_FIGURES,
        "code": CODE_DIR,
        "specs": SPECS_DIR,
        "state": STATE_DIR,
    }
    if key not in mapping:
        raise ValueError(f"Unknown path key: {key}")
    return mapping[key]

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    for p in [DATA_RAW, DATA_CURATED, DATA_RESULTS, DATA_FIGURES, STATE_DIR]:
        p.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "project_root": str(_PROJECT_ROOT),
        "random_seed": RANDOM_SEED,
        "model_config": {
            "gpu": MODEL_USE_GPU,
            "quantization_bits": MODEL_QUANTIZATION_BITS,
            "n_gpu_layers": MODEL_N_GPU_LAYERS,
        },
        "thresholds": {
            "complexity": COMPLEXITY_THRESHOLD,
            "hard_percentile": HARD_INSTANCE_PERCENTILE,
            "min_synthetic": MIN_SYNTHETIC_ISSUES,
            "validation_sample": VALIDATION_SAMPLE_SIZE,
            "coverage_column": COVERAGE_COLUMN_NAME,
            "sweep_sample": SWEEP_SAMPLE_SIZE,
            "turn_limits": TURN_LIMITS,
        },
        "dataset": {
            "name": HF_DATASET_NAME,
            "split": HF_DATASET_SPLIT,
        },
        "execution": {
            "max_hours": MAX_EXECUTION_HOURS,
            "ram_limit_gb": RAM_LIMIT_GB,
        },
        "generated_at": datetime.now().isoformat(),
    }