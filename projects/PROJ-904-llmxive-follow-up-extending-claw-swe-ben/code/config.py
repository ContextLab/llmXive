import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

# Configuration Constants
RANDOM_SEED = 42
BASELINE_N_LINES = 2048
MAX_CONTEXT_TOKENS = 8192

class StrategyType(str, Enum):
    BASELINE = "baseline"
    TFIDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARY = "semantic_summary"

class FailureType(str, Enum):
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"

@dataclass
class TaskInstance:
    instance_id: str
    repo: str
    issue_description: str
    test_patch: str
    line_count: int
    files_in_context: List[str]

@dataclass
class ContextConfiguration:
    strategy: StrategyType
    context_window: int
    max_snippets: int

@dataclass
class ExecutionResult:
    instance_id: str
    strategy: str
    model_size: str
    pass_at_1: bool
    duration_seconds: float
    failure_category: Optional[str] = None

def set_global_seeds(seed: int = RANDOM_SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_env_var(key: str, default: str = "") -> str:
    return os.getenv(key, default)

def get_hf_token() -> str:
    return get_env_var("HF_TOKEN", "")

def get_model_path(model_size: str) -> str:
    paths = {
        "1B": "meta-llama/Meta-Llama-3-8B-Instruct",  # Placeholder for 1B model
        "7B": "meta-llama/Meta-Llama-3-8B-Instruct",
    }
    return paths.get(model_size, paths["7B"])

def get_data_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "data")

def get_output_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "data", "intermediate")

def get_log_level() -> str:
    return get_env_var("LOG_LEVEL", "INFO")
