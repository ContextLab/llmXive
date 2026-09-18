import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

# Constitution Principle I: Hardcoded seeds for reproducibility
GLOBAL_SEED = 42
torch.manual_seed(GLOBAL_SEED)
np.random.seed(GLOBAL_SEED)
random.seed(GLOBAL_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(GLOBAL_SEED)

def set_global_seeds(seed: int = GLOBAL_SEED) -> None:
    """Explicitly set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_env_var(key: str, default: Optional[str] = None) -> str:
    """Retrieve an environment variable, raising if missing and no default."""
    val = os.getenv(key, default)
    if val is None:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return val

def get_hf_token() -> str:
    """Retrieve HuggingFace token from environment."""
    return get_env_var("HF_TOKEN")

def get_model_path(model_name: str) -> str:
    """Get model path from environment or default."""
    env_key = f"MODEL_PATH_{model_name.upper()}"
    return get_env_var(env_key, f"models/{model_name}")

def get_data_dir() -> str:
    """Get the project data directory."""
    return get_env_var("DATA_DIR", "data")

def get_output_dir() -> str:
    """Get the project output directory."""
    return get_env_var("OUTPUT_DIR", "data/intermediate")

def get_log_level() -> int:
    """Get log level from environment."""
    level_str = get_env_var("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_str, logging.INFO)

class StrategyType(str, Enum):
    BASELINE = "baseline"
    TFIDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC = "semantic"

class FailureType(str, Enum):
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"

@dataclass
class TaskInstance:
    instance_id: str
    problem_statement: str
    repo: str
    base_commit: str
    patch: str
    test_patch: str
    file_paths: List[str] = field(default_factory=list)

@dataclass
class ContextConfiguration:
    strategy: StrategyType
    context_window: int
    max_tokens: int
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    instance_id: str
    model_id: str
    strategy: str
    status: str
    pass_: bool
    output: str
    duration: float
    tokens_used: int
    error: Optional[str] = None