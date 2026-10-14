"""
Project configuration: paths, seeds, and hyperparameters.

This module centralizes all configuration constants to ensure consistency
across the codebase.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"
LOG_DIR = PROJECT_ROOT / "logs"

# Canonical path constants (task T002)
DATA_RAW = RAW_DATA_DIR
DATA_PROCESSED = PROCESSED_DATA_DIR
RESULTS_DIR = DATA_DIR / "results"

# Random seeds for reproducibility
RANDOM_SEED = 42
NUMPY_SEED = 42
SEED = RANDOM_SEED  # canonical seed used for jitter generation

# Hyperparameters for latency injection
LATENCY_MIN_MS = 200
LATENCY_MAX_MS = 2000
LATENCY_JITTER_MS = 50
DELAY_VALUES = list(range(200, 2001, 200))

# Audio processing constraints
MAX_AUDIO_DURATION_SEC = 300  # 5 minutes max
CHUNK_SIZE_SEC = 5  # Process in 5-second chunks
SAMPLE_RATE = 22050  # Standard for EVA-Bench

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# File paths
TTS_CHARACTERISTICS_PATH = PROJECT_ROOT / "docs" / "tts_characteristics.md"
CHECKSUMS_PATH = DATA_DIR / "checksums.json"
TURN_BOUNDARIES_PATH = PROCESSED_DATA_DIR / "turn_boundaries.csv"
RESULTS_PATH = PROCESSED_DATA_DIR / "results.csv"
STATISTICAL_REPORT_PATH = PROCESSED_DATA_DIR / "statistical_report.json"

# Dataset source (task T004): canonical public HuggingFace URL for the
# EVA-Bench dataset archive. Can be overridden via environment variable.
DATASET_URL = os.getenv(
    "EVA_BENCH_DATASET_URL",
    "https://huggingface.co/datasets/amazon-science/EVA-Bench/resolve/main/eva_bench_dataset.zip",
)
# Upstream-pinned SHA-256 hashes (filename -> hex digest). Empty means
# hashes are computed from the freshly downloaded files and recorded in
# data/checksums.json for subsequent integrity verification.
DATASET_CHECKSUMS: Dict[str, str] = {}

# Validation thresholds
MIN_SILENCE_FOR_GAP_SHIFT_MS = 50
MAX_GAP_OVERLAP_MS = 10

# Evaluation settings
EVA_BENCH_TIMEOUT_SEC = 300
MAX_RETRIES = 3

# Constants for acoustic perturbation
SNR_MIN_DB = 0
SNR_MAX_DB = 30

# Statistical analysis parameters
KNEE_POINT_TOLERANCE_MS = 50
P_VALUE_THRESHOLD = 0.05


def set_global_seed(seed: int = SEED) -> None:
    """Seed Python's `random` module (and numpy if available) for
    reproducible jitter generation and any stochastic processing."""
    global SEED
    SEED = int(seed)
    random.seed(SEED)
    try:
        import numpy as np

        np.random.seed(SEED)
    except ImportError:
        pass


# Ensure directories exist
def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    for dir_path in [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DIR,
        CODE_DIR,
        TESTS_DIR,
        SPECS_DIR,
        LOG_DIR,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

# Export all configuration
__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "DATA_RAW",
    "DATA_PROCESSED",
    "RESULTS_DIR",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "CODE_DIR",
    "TESTS_DIR",
    "SPECS_DIR",
    "LOG_DIR",
    "RANDOM_SEED",
    "NUMPY_SEED",
    "SEED",
    "set_global_seed",
    "LATENCY_MIN_MS",
    "LATENCY_MAX_MS",
    "LATENCY_JITTER_MS",
    "DELAY_VALUES",
    "MAX_AUDIO_DURATION_SEC",
    "CHUNK_SIZE_SEC",
    "SAMPLE_RATE",
    "LOG_LEVEL",
    "LOG_MAX_BYTES",
    "LOG_BACKUP_COUNT",
    "TTS_CHARACTERISTICS_PATH",
    "CHECKSUMS_PATH",
    "TURN_BOUNDARIES_PATH",
    "RESULTS_PATH",
    "STATISTICAL_REPORT_PATH",
    "DATASET_URL",
    "DATASET_CHECKSUMS",
    "MIN_SILENCE_FOR_GAP_SHIFT_MS",
    "MAX_GAP_OVERLAP_MS",
    "EVA_BENCH_TIMEOUT_SEC",
    "MAX_RETRIES",
    "SNR_MIN_DB",
    "SNR_MAX_DB",
    "KNEE_POINT_TOLERANCE_MS",
    "P_VALUE_THRESHOLD",
    "ensure_directories",
]
