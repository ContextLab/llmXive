"""
Project configuration for llmXive follow-up: extending SWE-Explore.

Defines paths, random seeds, and model configuration (CPU-only).
"""

import os
from pathlib import Path
from typing import Final

# Project Root
_ROOT: Final = Path(__file__).resolve().parent.parent

# --- Path Configuration ---
# Data directories
DATA_RAW: Final = _ROOT / "data" / "raw"
DATA_CURATED: Final = _ROOT / "data" / "curated"
DATA_RESULTS: Final = _ROOT / "data" / "results"

# Ensure directories exist
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_CURATED.mkdir(parents=True, exist_ok=True)
DATA_RESULTS.mkdir(parents=True, exist_ok=True)

# Output paths for specific artifacts
HARD_SUBSET_PATH: Final = DATA_CURATED / "hard_subset.jsonl"
SYNTHETIC_ISSUES_PATH: Final = DATA_CURATED / "synthetic_issues.jsonl"
VALIDATION_REPORT_PATH: Final = DATA_CURATED / "validation_report.md"
PAIRED_METRICS_PATH: Final = DATA_RESULTS / "paired_metrics.json"
FINAL_METRICS_PATH: Final = DATA_RESULTS / "final_metrics.json"
PAPER_DRAFT_PATH: Final = _ROOT / "paper" / "draft.md"

# --- Random Seeds ---
# Fixed seed for reproducibility
RANDOM_SEED: Final = 42

# --- Model Configuration ---
# CPU-only constraints per project requirements
MODEL_DEVICE: Final = "cpu"
MAX_MODEL_SIZE_GB: Final = 4.0  # Approximate limit for 7GB RAM constraint
TORCH_NUM_THREADS: Final = 2    # Match 2-core constraint

# --- Hyperparameters & Thresholds ---
# Derived from tasks.md specifications
# T015a: Resolving deferred values for hard instance selection and validation sampling
HARD_INSTANCE_PERCENTILE: Final = 20  # Bottom 20% for "Hard" instances (FR-001)
VALIDATION_SAMPLE_SIZE: Final = 20    # N=20 for manual inspection (FR-009)

ITERATIVE_TURN_LIMIT: Final = 3       # Max turns per SC-006
BASELINE_QUERY_COUNT: Final = 3       # 3 parallel queries for baseline (US2)
SWEEP_SAMPLE_SIZE: Final = 20         # N=20 issues for turn-limit sweep (SC-006)

# --- Execution Constraints ---
# SC-005: Total execution time limit
MAX_EXECUTION_HOURS: Final = 6.0
RUNTIME_MONITOR_THRESHOLD_HOURS: Final = 5.5

# --- Logging & Debugging ---
LOG_LEVEL: Final = "INFO"
VERBOSE: Final = False

# --- Helper Functions ---
def get_config_summary() -> dict:
    """Return a summary of the current configuration."""
    return {
        "paths": {
            "data_raw": str(DATA_RAW),
            "data_curated": str(DATA_CURATED),
            "data_results": str(DATA_RESULTS),
        },
        "random_seed": RANDOM_SEED,
        "model_device": MODEL_DEVICE,
        "turn_limit": ITERATIVE_TURN_LIMIT,
        "hard_instance_percentile": HARD_INSTANCE_PERCENTILE,
        "validation_sample_size": VALIDATION_SAMPLE_SIZE,
    }