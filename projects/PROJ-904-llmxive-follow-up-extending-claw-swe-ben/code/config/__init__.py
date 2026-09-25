"""
Configuration module for llmXive project.
Exports all configuration utilities and constants.
"""
import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

# Constants
RANDOM_SEED = 42
HF_TOKEN = os.getenv("HF_TOKEN", "")
MODEL_PATH = os.getenv("MODEL_PATH", "meta-llama/Llama-2-7b-hf")

class StrategyType(Enum):
    BASELINE = "baseline"
    TF_IDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARY = "semantic_summary"

class FailureType(Enum):
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"

@dataclass
class TaskInstance:
    instance_id: str
    repo: str
    base_commit: str
    patch: str
    test_patch: str
    problem_statement: str
    hints: List[str] = field(default_factory=list)
    environment_setup_commit: Optional[str] = None

@dataclass
class ContextConfiguration:
    strategy: StrategyType
    max_context_tokens: int = 4096
    retrieval_k: int = 5
    include_dependencies: bool = True

@dataclass
class ExecutionResult:
    instance_id: str
    model_size: str
    strategy: str
    pass_status: bool
    execution_time: float
    tokens_used: int
    error_message: Optional[str] = None
    failure_category: Optional[FailureType] = None

def set_global_seeds(seed: int = RANDOM_SEED):
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_env_var(name: str, default: Optional[str] = None) -> str:
    """Get environment variable with optional default."""
    return os.getenv(name, default if default is not None else "")

def get_hf_token() -> str:
    """Get Hugging Face token from environment."""
    return get_env_var("HF_TOKEN")

def get_model_path() -> str:
    """Get model path from environment or default."""
    return get_env_var("MODEL_PATH", MODEL_PATH)

def get_data_dir() -> str:
    """Get data directory path."""
    return get_env_var("DATA_DIR", "data")

def get_output_dir() -> str:
    """Get output directory path."""
    return get_env_var("OUTPUT_DIR", "data")

def get_log_level() -> str:
    """Get log level from environment."""
    return get_env_var("LOG_LEVEL", "INFO")
