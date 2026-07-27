"""
Configuration module for llmXive.
Defines paths, random seeds, model config, and critical thresholds.
"""
import os
from pathlib import Path
from typing import Final, Dict, Any
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

# Random Seeds
RANDOM_SEED: Final = 42
SWEEP_SEED: Final = 42

# Model Config (CPU-only, 8-bit quantization default)
MODEL_USE_GPU: Final = False
MODEL_QUANTIZATION_BITS: Final = 8
MODEL_N_GPU_LAYERS: Final = 0
MODEL_MAX_CONTEXT: Final = 4096

# Critical Thresholds
COMPLEXITY_THRESHOLD: Final = 50
HARD_INSTANCE_PERCENTILE: Final = 0.20
MIN_SYNTHETIC_ISSUES: Final = 10
VALIDATION_SAMPLE_SIZE: Final = 5
COVERAGE_COLUMN_NAME: Final = 'initial_coverage'
TIE_THRESHOLD: Final = 0.10
SWEEP_SAMPLE_SIZE: Final = 100

# Execution Constraints
MAX_EXECUTION_HOURS: Final = 6.0
RAM_LIMIT_GB: Final = 7.0

# Dataset Source
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
    }
    if key not in mapping:
        raise ValueError(f"Unknown path key: {key}")
    return mapping[key]

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    for p in [DATA_RAW, DATA_CURATED, DATA_RESULTS, DATA_FIGURES]:
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
            "tie_threshold": TIE_THRESHOLD,
            "sweep_sample": SWEEP_SAMPLE_SIZE,
        },
        "dataset": {
            "name": HF_DATASET_NAME,
            "split": HF_DATASET_SPLIT,
        },
        "generated_at": datetime.now().isoformat(),
    }