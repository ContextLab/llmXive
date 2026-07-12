"""
Global configuration for the LlmXive Follow-up project.
Defines paths, random seeds, and memory limits for the pipeline.
"""
import os
import random
import numpy as np
from pathlib import Path
from typing import Final

# --- Project Roots ---
# All paths are relative to the project root (where this file resides or is invoked from)
# We assume the project root is the parent of 'code'
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
CODE_ROOT: Final[Path] = PROJECT_ROOT / "code"
DATA_ROOT: Final[Path] = PROJECT_ROOT / "data"
RESULTS_ROOT: Final[Path] = PROJECT_ROOT / "results"
SPECS_ROOT: Final[Path] = PROJECT_ROOT / "specs"
TESTS_ROOT: Final[Path] = PROJECT_ROOT / "tests"
CONTRACTS_ROOT: Final[Path] = PROJECT_ROOT / "contracts"

# --- Data Subdirectories ---
DATA_RAW: Final[Path] = DATA_ROOT / "raw"
DATA_PROCESSED: Final[Path] = DATA_ROOT / "processed"
DATA_EMBEDDINGS: Final[Path] = DATA_ROOT / "embeddings"

# --- Results Subdirectories ---
RESULTS_METRICS: Final[Path] = RESULTS_ROOT / "metrics"
RESULTS_REPORTS: Final[Path] = RESULTS_ROOT / "reports"
RESULTS_METHOD_NOTES: Final[Path] = RESULTS_ROOT / "methodology_notes"

# --- Random Seeds ---
# Fixed seed for reproducibility across numpy, python, and torch (if used)
# T004 Requirement: Global random seeds
RANDOM_SEED: Final[int] = 42
NUMPY_SEED: Final[int] = 42
TORCH_SEED: Final[int] = 42  # Used if torch is imported later, set here for consistency

def set_seed(seed: int = RANDOM_SEED) -> None:
    """
    Set global random seeds for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Attempt to set torch seed if available, fail gracefully if not
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# --- Memory Limits (Constitution Principle: Limited Capacity) ---
# T004 Requirement: Memory limits (limited capacity)
# Hard limit for peak RAM usage in GB to prevent OOM on free-tier CI
MEMORY_LIMIT_GB: Final[float] = 6.5
MEMORY_LIMIT_BYTES: Final[int] = int(MEMORY_LIMIT_GB * 1024 * 1024 * 1024)

# Batch size for embedding extraction (tuned for memory limit)
# Adjust based on encoder dimension and audio length
EMBEDDING_BATCH_SIZE: Final[int] = 16

# --- Encoder Configuration ---
# Primary encoder (Distil-Whisper)
ENCODER_PRIMARY: Final[str] = "distil-whisper/distil-large-v2"
# Fallback encoder (OpenAI Whisper Distil Base)
ENCODER_FALLBACK: Final[str] = "openai/whisper-distil-base"

# --- Dataset Configuration ---
# Real data source identifiers
DATASET_HUB_ID: Final[str] = "audio_bench/jailbreak_v1"
DATASET_FALLBACK_ID: Final[str] = "audio_bench"

# --- Runtime Constraints ---
# Maximum allowed runtime for the full pipeline (in seconds)
# 6 hours * 3600 seconds
MAX_RUNTIME_SECONDS: Final[int] = 6 * 3600

def ensure_directories() -> None:
    """
    Create all required directory structures if they do not exist.
    """
    directories = [
        DATA_RAW,
        DATA_PROCESSED,
        DATA_EMBEDDINGS,
        RESULTS_METRICS,
        RESULTS_REPORTS,
        RESULTS_METHOD_NOTES,
        CONTRACTS_ROOT,
        SPECS_ROOT,
        TESTS_ROOT,
        CODE_ROOT / "utils",
        CODE_ROOT / "models",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)