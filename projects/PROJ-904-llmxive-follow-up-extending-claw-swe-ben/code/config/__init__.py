"""
Configuration module for llmXive project.
Provides environment variable management, random seed pinning, and model paths.
"""
import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

# Constitution Principle I: Hardcoded seeds
GLOBAL_SEED = 42

class StrategyType(Enum):
    """Enumeration of context processing strategies."""
    BASELINE = "baseline"
    TFIDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARIZATION = "summarization"

class FailureType(Enum):
    """Enumeration of failure types."""
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"

@dataclass
class TaskInstance:
    """Data model for a task instance."""
    instance_id: str
    issue_description: str
    patch: str
    repo: str
    base_commit: str
    file_history: List[Dict[str, Any]]

@dataclass
class ContextConfiguration:
    """Data model for context configuration."""
    strategy: StrategyType
    max_tokens: int
    relevant_lines_threshold: int
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    """Data model for execution result."""
    instance_id: str
    strategy: str
    model_size: str
    pass_status: bool
    log: str
    duration: float

def set_global_seeds(seed: int = GLOBAL_SEED) -> None:
    """
    Pin random seeds for reproducibility.
    Constitution Principle I.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_env_var(key: str, default: Optional[str] = None) -> str:
    """Get an environment variable or return default."""
    val = os.getenv(key, default)
    if val is None:
        raise ValueError(f"Environment variable {key} is not set")
    return val

def get_hf_token() -> str:
    """Get Hugging Face token from environment."""
    return get_env_var("HF_TOKEN")

def get_model_path(model_name: str) -> str:
    """Get the path to a model from environment or default mapping."""
    defaults = {
        "1b": "meta-llama/Llama-3.2-1B-Instruct",
        "7b": "meta-llama/Llama-3.2-7B-Instruct",
    }
    return os.getenv(f"MODEL_PATH_{model_name.upper()}", defaults.get(model_name, model_name))

def get_data_dir() -> str:
    """Get the data directory path."""
    return get_env_var("DATA_DIR", "data")

def get_output_dir() -> str:
    """Get the output directory path."""
    return get_env_var("OUTPUT_DIR", "data/intermediate")

def get_log_level() -> str:
    """Get the log level from environment."""
    return get_env_var("LOG_LEVEL", "INFO")
