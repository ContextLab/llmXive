"""
Configuration module for the llmXive project PROJ-151.

Defines global constants, file paths, and enforces reproducibility by
setting random seeds for random, numpy, and torch.
"""

import os
import random
from pathlib import Path

import numpy as np

# Attempt to import torch; if unavailable, seed setting will be skipped for torch
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# --- Global Constants ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED = 42
MAX_LOC = 30
MIN_COMMENT_LENGTH = 10
FORBIDDEN_COMMENT_PATTERNS = ["LGTM", "lgtm"]
ALLOWED_LANGUAGES = ["Java", "Python"]
DATASET_NAME = "loubnabnl/prs-v2-sample"

# --- Directory Paths ---
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_GENERATED_DIR = DATA_DIR / "generated"
DATA_VALIDATION_DIR = DATA_DIR / "validation"
FIGURES_DIR = PROJECT_ROOT / "figures"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

# Output file paths
FILTERED_PRS_PATH = DATA_PROCESSED_DIR / "filtered_prs.parquet"
CODE_SNIPPETS_PATH = DATA_GENERATED_DIR / "code_snippets.csv"
METRICS_PATH = DATA_PROCESSED_DIR / "metrics.csv"
PROVENANCE_PATH = DATA_GENERATED_DIR / "generated_provenance.csv"
STATE_FILE_PATH = PROJECT_ROOT / "state.yaml"
SURVEY_RESULTS_PATH = DATA_VALIDATION_DIR / "survey_results.csv"

# --- Reproducibility ---
def set_global_seed(seed: int = SEED) -> None:
    """
    Sets the random seed for random, numpy, and torch (if available)
    to ensure reproducibility across runs.

    Args:
        seed (int): The integer seed value. Defaults to 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

# Initialize seed immediately upon module import
set_global_seed(SEED)
