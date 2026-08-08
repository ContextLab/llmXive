"""
Configuration management for the llmXive automated science pipeline.

This module centralizes random seeds, file paths, and API credentials
to ensure reproducibility and consistent environment setup across the project.
"""

import os
import random
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import yaml

# Project Root
# Assumes this file is at code/utils/config.py, so root is 3 levels up
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# --- Path Constants ---
DATA_DIR = _PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
CODE_DIR = _PROJECT_ROOT / "code"
TESTS_DIR = _PROJECT_ROOT / "tests"
DOCS_DIR = _PROJECT_ROOT / "docs"

# Specific Output Paths (matching tasks.md requirements)
GENERATED_SNIPPETS_PATH = DATA_PROCESSED_DIR / "generated_snippets.parquet"
DIAGNOSTIC_SCORES_PATH = DATA_PROCESSED_DIR / "diagnostic_scores.parquet"
PROMPT_BASED_COHORT_PATH = DATA_PROCESSED_DIR / "prompt_based_cohort.parquet"
SENSITIVITY_SUMMARY_PATH = DATA_PROCESSED_DIR / "sensitivity_summary.json"
DEVIATION_REPORT_PATH = DATA_PROCESSED_DIR / "deviation_report.md"
MATCHING_FAILURE_REPORT_PATH = DATA_PROCESSED_DIR / "matching_failure_report.json"
SPEC_AMENDMENT_REQUEST_PATH = _PROJECT_ROOT / "spec_amendment_request.md"

# Checksums file
CHECKSUMS_PATH = DATA_DIR / "checksums.yaml"

# --- Random Seeds ---
DEFAULT_SEED = 42

def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch (if available).
    
    Args:
        seed: The random seed to use. Defaults to DEFAULT_SEED if None.
    
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    # Python built-in
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # PyTorch (optional, only if installed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    
    return seed

# --- API Credentials ---
# Reads from environment variables to avoid hardcoding secrets.
# Raises KeyError if not found, ensuring the pipeline fails loudly if credentials are missing.

GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError(
        "GITHUB_TOKEN environment variable is not set. "
        "Please set it to your GitHub Personal Access Token to proceed."
    )

# --- Configuration Dictionary ---
CONFIG: Dict[str, Any] = {
    "project_root": str(_PROJECT_ROOT),
    "paths": {
        "data": str(DATA_DIR),
        "data_raw": str(DATA_RAW_DIR),
        "data_processed": str(DATA_PROCESSED_DIR),
        "code": str(CODE_DIR),
        "tests": str(TESTS_DIR),
        "docs": str(DOCS_DIR),
        "generated_snippets": str(GENERATED_SNIPPETS_PATH),
        "diagnostic_scores": str(DIAGNOSTIC_SCORES_PATH),
        "prompt_based_cohort": str(PROMPT_BASED_COHORT_PATH),
        "sensitivity_summary": str(SENSITIVITY_SUMMARY_PATH),
        "deviation_report": str(DEVIATION_REPORT_PATH),
        "matching_failure_report": str(MATCHING_FAILURE_REPORT_PATH),
        "spec_amendment_request": str(SPEC_AMENDMENT_REQUEST_PATH),
        "checksums": str(CHECKSUMS_PATH),
    },
    "seeds": {
        "default": DEFAULT_SEED,
    },
    "api": {
        "github_token_available": GITHUB_TOKEN is not None,
    }
}

def get_config() -> Dict[str, Any]:
    """Return the full configuration dictionary."""
    return CONFIG.copy()

def ensure_directories() -> None:
    """Ensure all required directories exist. Creates them if missing."""
    dirs = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        CODE_DIR,
        TESTS_DIR,
        DOCS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Initialize directories on import to satisfy T001/T001d requirements implicitly
ensure_directories()