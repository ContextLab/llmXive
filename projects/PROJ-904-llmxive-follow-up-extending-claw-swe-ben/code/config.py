import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

# Constitution Principle I: Reproducibility via Hardcoded Seeds
# These seeds are global constants used to ensure deterministic behavior
# across all experiments, regardless of hardware or library version (to the extent possible).
GLOBAL_SEED = 42
TORCH_SEED = 42
NUMPY_SEED = 42
PYTHON_SEED = 42

def set_global_seeds(seed: int = GLOBAL_SEED) -> None:
    """
    Set random seeds for Python, NumPy, and PyTorch to ensure reproducibility.
    This function must be called at the very beginning of any experiment script.
    
    Args:
        seed: The integer seed to use for all random number generators.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # For multi-GPU
        # Ensure deterministic behavior in CuDNN
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    # Log the seed being used for audit purposes
    import logging
    logging.getLogger(__name__).info(f"Global seeds set to: {seed}")

# Environment Variable Management
def get_env_var(key: str, default: Optional[str] = None) -> str:
    """
    Retrieve an environment variable, raising an error if missing and no default provided.
    
    Args:
        key: The environment variable name.
        default: Optional default value if the variable is not set.
        
    Returns:
        The value of the environment variable.
        
    Raises:
        ValueError: If the variable is missing and no default is provided.
    """
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable '{key}' is not set and no default provided.")
    return value

def get_hf_token() -> str:
    """
    Retrieve the Hugging Face token from environment variables.
    
    This token is required for accessing gated models (e.g., Llama-3) on Hugging Face Hub.
    The token must be set in the environment before running any model loading scripts.
    
    Returns:
        The Hugging Face access token.
        
    Raises:
        ValueError: If HF_TOKEN is not set in the environment.
    """
    return get_env_var("HF_TOKEN")

def get_model_path(model_name: str) -> str:
    """
    Construct the full path to a model, either from environment or default location.
    
    This function checks for specific environment variables for known models first,
    then falls back to a standard cache directory structure.
    
    Args:
        model_name: The name of the model (e.g., 'meta-llama/Llama-3-1B').
        
    Returns:
        The path string.
        
    Example:
        If MODEL_PATH_META_LLAMA_Llama-3-1B is set, returns that value.
        Otherwise, returns DATA_DIR/models/Llama-3-1B.
    """
    base_dir = get_data_dir()
    # Check if model is cached in a specific env var first
    # Sanitize model name for env var usage (replace / with _)
    env_key_suffix = model_name.replace('/', '_').upper()
    env_key = f"MODEL_PATH_{env_key_suffix}"
    
    if os.getenv(env_key):
        return os.getenv(env_key)
    
    # Default fallback to local cache structure
    # Extract just the model identifier (last part of the path)
    model_identifier = model_name.split("/")[-1]
    return os.path.join(base_dir, "models", model_identifier)

def get_data_dir() -> str:
    """
    Get the root data directory from environment or default.
    
    Returns:
        The path to the data directory.
    """
    return get_env_var("DATA_DIR", default="data")

def get_output_dir() -> str:
    """
    Get the root output directory from environment or default.
    
    Returns:
        The path to the output directory.
    """
    return get_env_var("OUTPUT_DIR", default="data/results")

def get_log_level() -> int:
    """
    Get the logging level from environment, defaulting to INFO.
    
    Returns:
        An integer logging level (e.g., logging.INFO, logging.DEBUG).
    """
    level_str = get_env_var("LOG_LEVEL", default="INFO")
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    return levels.get(level_str, logging.INFO)

# Data Models (Constitution Principle III: Schema Enforcement)
class FailureType(Enum):
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"
    OTHER = "other"

class StrategyType(Enum):
    BASELINE = "baseline"
    TF_IDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARY = "semantic_summary"

@dataclass
class TaskInstance:
    """
    Represents a single task instance from the dataset.
    Corresponds to the task_instance.schema.yaml.
    """
    instance_id: str
    problem_statement: str
    repo: str
    version: str
    base_commit: str
    patch: str
    test_patch: str
    # Calculated fields
    relevant_lines_count: int = 0
    import_graph_nodes: int = 0
    import_graph_edges: int = 0

@dataclass
class ContextConfiguration:
    """
    Configuration for how context is processed and injected.
    Corresponds to the context_config.schema.yaml.
    """
    strategy: StrategyType
    max_tokens: int
    truncation_strategy: str = "first_n"  # first_n, last_n, smart_truncate
    include_imports: bool = True
    include_docstrings: bool = True
    # Strategy-specific params
    tfidf_k: int = 10  # Top-K snippets for TF-IDF
    diff_window_size: int = 50  # Lines around diff for Diff-Aware
    semantic_threshold: float = 0.65  # Similarity threshold for summarization

@dataclass
class ExecutionResult:
    """
    Result of running a model against a task instance.
    Corresponds to the execution_result.schema.yaml.
    """
    instance_id: str
    strategy: StrategyType
    model_size: str  # e.g., "1B", "7B"
    success: bool
    output_patch: Optional[str] = None
    log_output: Optional[str] = None
    execution_time_seconds: float = 0.0
    tokens_generated: int = 0
    failure_type: Optional[FailureType] = None
    failure_reason: Optional[str] = None
    seed_used: int = GLOBAL_SEED