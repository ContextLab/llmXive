"""
Configuration management for the llmXive project.

This module handles environment variables, global seeds, and constant definitions
required across the research pipeline.
"""

import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

# Global Configuration
RANDOM_SEED = 42
BASELINE_N_LINES = 2048

# Environment Variable Keys
HF_TOKEN_KEY = "HF_TOKEN"
MODEL_PATH_KEY = "MODEL_PATH"
LOG_LEVEL_KEY = "LOG_LEVEL"

# Strategy Types
class StrategyType(Enum):
    BASELINE = "baseline"
    TF_IDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARY = "semantic_summary"

# Failure Types
class FailureType(Enum):
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    OOM = "oom"


@dataclass
class TaskInstance:
    instance_id: str
    repo: str
    base_commit: str
    patch: str
    test_patch: str
    problem_statement: str
    hints: List[str] = field(default_factory=list)
    version: str = "0.0.0"
    pass_at_1: Optional[float] = None
    status: str = "pending"


@dataclass
class ContextConfiguration:
    strategy: StrategyType
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    seed: int = RANDOM_SEED


@dataclass
class ExecutionResult:
    instance_id: str
    model_id: str
    strategy: str
    status: str
    pass_at_1: float
    duration_seconds: float
    error_message: Optional[str] = None
    tokens_used: int = 0


def set_global_seeds(seed: Optional[int] = None) -> None:
    """
    Set global random seeds for reproducibility.

    Args:
        seed: Random seed value. Uses RANDOM_SEED if None.
    """
    if seed is None:
        seed = RANDOM_SEED

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable.

    Args:
        key: Environment variable key.
        default: Default value if not found.

    Returns:
        The environment variable value or default.
    """
    return os.getenv(key, default)


def get_hf_token() -> Optional[str]:
    """
    Get the Hugging Face token from environment.

    Returns:
        The HF token or None.
    """
    return get_env_var(HF_TOKEN_KEY)


def get_model_path() -> Optional[str]:
    """
    Get the model path from environment.

    Returns:
        The model path or None.
    """
    return get_env_var(MODEL_PATH_KEY)


def get_data_dir() -> Path:
    """
    Get the data directory path.

    Returns:
        Path to the data directory.
    """
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_output_dir() -> Path:
    """
    Get the output directory path.

    Returns:
        Path to the output directory.
    """
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_log_level() -> int:
    """
    Get the log level from environment.

    Returns:
        Logging level constant.
    """
    level_str = get_env_var(LOG_LEVEL_KEY, "INFO")
    levels = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
    return levels.get(level_str.upper(), 20)
