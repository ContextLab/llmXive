"""
Configuration management for llmXive project.
Exports: StrategyType, FailureType, TaskInstance, ContextConfiguration, ExecutionResult, 
         set_global_seeds, get_env_var, get_hf_token, get_model_path, get_data_dir, get_output_dir, get_log_level
"""
import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import logging

# --- Enums ---
class StrategyType(Enum):
    BASELINE = "baseline"
    TF_IDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARY = "semantic_summarization"

class FailureType(Enum):
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    OOM = "oom"
    UNKNOWN = "unknown"

# --- Dataclasses ---
@dataclass
class TaskInstance:
    instance_id: str
    description: str
    repo_name: str
    patch: str
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ContextConfiguration:
    strategy: StrategyType
    max_tokens: int = 2048
    temperature: float = 0.0
    top_p: float = 1.0
    seed: int = 42

@dataclass
class ExecutionResult:
    instance_id: str
    strategy: str
    model_size: str
    pass_status: bool
    duration_seconds: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- Configuration Functions ---
def set_global_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_env_var(key: str, default: Optional[str] = None) -> str:
    """Get an environment variable or raise an error if missing (unless default provided)."""
    val = os.getenv(key)
    if val is None:
        if default is not None:
            return default
        raise ValueError(f"Environment variable {key} is not set.")
    return val

def get_hf_token() -> str:
    """Get Hugging Face token from environment."""
    return get_env_var("HF_TOKEN")

def get_model_path(model_name: str) -> str:
    """Get model path from environment or default."""
    # Map model names to paths if needed
    defaults = {
        "1b": "meta-llama/Llama-3.2-1B-Instruct",
        "7b": "meta-llama/Llama-3.1-8B-Instruct"
    }
    return os.getenv(f"MODEL_PATH_{model_name.upper()}", defaults.get(model_name, model_name))

def get_data_dir() -> Path:
    """Get the data directory path."""
    from pathlib import Path
    base = Path(os.getenv("DATA_DIR", "data"))
    base.mkdir(parents=True, exist_ok=True)
    return base

def get_output_dir() -> Path:
    """Get the output directory path."""
    from pathlib import Path
    base = Path(os.getenv("OUTPUT_DIR", "data"))
    base.mkdir(parents=True, exist_ok=True)
    return base

def get_log_level() -> int:
    """Get log level from environment."""
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_str, logging.INFO)

# --- Imports for API Surface ---
# Ensure these are available at module level for imports like:
# from config import StrategyType, ...
__all__ = [
    'StrategyType', 'FailureType', 'TaskInstance', 'ContextConfiguration', 'ExecutionResult',
    'set_global_seeds', 'get_env_var', 'get_hf_token', 'get_model_path', 
    'get_data_dir', 'get_output_dir', 'get_log_level'
]

# Import Path at module level to avoid circular imports in type hints if necessary
from pathlib import Path