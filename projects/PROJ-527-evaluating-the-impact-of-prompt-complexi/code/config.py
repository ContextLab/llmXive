"""
Configuration management for the llmXive prompt complexity evaluation pipeline.

This module provides centralized configuration including:
- Fixed random seeds for reproducibility
- Project directory paths
- API keys and credentials (loaded from environment variables)
- Runtime parameters

All paths are resolved relative to the project root.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

# ============================================================================
# Project Root
# ============================================================================
# Determine project root by looking for the .git directory or the
# 'data' directory which we know exists from T002/T005.
_CURRENT_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _CURRENT_FILE.parent.parent
if not (_PROJECT_ROOT / "data").exists():
    # Fallback: assume current working directory if script moved
    _PROJECT_ROOT = Path.cwd()

# ============================================================================
# Random Seeds (Fixed for Reproducibility)
# ============================================================================
RANDOM_SEED = 42
PYTHON_SEED = RANDOM_SEED
NUMPY_SEED = RANDOM_SEED
TORCH_SEED = RANDOM_SEED  # For future compatibility if PyTorch is added

# Set seeds immediately upon import to ensure reproducibility
random.seed(PYTHON_SEED)
np.random.seed(NUMPY_SEED)

# ============================================================================
# Directory Paths
# ============================================================================
class Paths:
    """Centralized path definitions relative to the project root."""

    ROOT: Path = _PROJECT_ROOT
    CODE: Path = ROOT / "code"
    DATA: Path = ROOT / "data"
    DATA_RAW: Path = DATA / "raw"
    DATA_PROCESSED: Path = DATA / "processed"
    DATA_RESULTS: Path = DATA / "results"
    STATE: Path = ROOT / "state"
    TESTS: Path = ROOT / "tests"
    FIGURES: Path = DATA / "figures"
    SPECS: Path = ROOT / "specs"

    # Ensure directories exist
    @classmethod
    def ensure_dirs(cls) -> None:
        """Create all required directories if they do not exist."""
        cls.DATA_RAW.mkdir(parents=True, exist_ok=True)
        cls.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        cls.DATA_RESULTS.mkdir(parents=True, exist_ok=True)
        cls.STATE.mkdir(parents=True, exist_ok=True)
        cls.FIGURES.mkdir(parents=True, exist_ok=True)

# ============================================================================
# API Keys and Credentials
# ============================================================================
def get_env_var(name: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Retrieve an environment variable.

    Args:
        name: Environment variable name.
        default: Default value if not set.
        required: If True, raise an error if not set.

    Returns:
        The value of the environment variable.

    Raises:
        ValueError: If required is True and the variable is not set.
    """
    value = os.getenv(name, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{name}' is not set.")
    return value if value is not None else ""

# HuggingFace Inference API Key
HF_API_KEY: str = get_env_var("HF_API_KEY", required=False)

# ============================================================================
# Runtime Configuration
# ============================================================================
class Config:
    """Runtime configuration parameters."""

    # LLM Settings
    LLM_MODEL: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    LLM_MAX_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT: int = 60
    LLM_RETRIES: int = 3

    # Execution Settings
    EXECUTION_TIMEOUT: int = 30
    EXECUTION_MAX_WORKERS: int = 4

    # Analysis Settings
    STAT_SIG_LEVEL: float = 0.05
    BONFERRONI_CORRECTION: bool = True

    # Tokenization
    TOKENIZER_NAME: str = "cl100k_base"  # tiktoken encoding

    # Complexity Thresholds (Token Counts)
    COMPLEXITY_SIMPLE_MAX: int = 50
    COMPLEXITY_MODERATE_MAX: int = 150
    COMPLEXITY_COMPLEX_MAX: int = 300
    COMPLEXITY_VERY_COMPLEX_MAX: int = 500

    # Degenerate Prompt Delta Threshold
    DEGENERATE_DELTA_THRESHOLD: int = 100

# Instantiate global config
config = Config()

# ============================================================================
# Helper Functions
# ============================================================================
def get_project_id() -> str:
    """Return the project ID extracted from the current directory name."""
    return _PROJECT_ROOT.name

def get_config_summary() -> Dict[str, Any]:
    """Return a dictionary of current configuration for logging/debugging."""
    return {
        "project_root": str(Paths.ROOT),
        "random_seed": RANDOM_SEED,
        "hf_api_key_set": bool(HF_API_KEY),
        "llm_model": config.LLM_MODEL,
        "execution_timeout": config.EXECUTION_TIMEOUT,
    }

# Ensure directories exist on module load
Paths.ensure_dirs()
