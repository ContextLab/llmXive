"""
Configuration and environment setup.
Manages environment variables for model paths, timeouts, and random seeds.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Directories to ensure exist
DIRECTORIES = [
    DATA_DIR,
    DATA_DIR / "raw",
    DATA_DIR / "processed",
    DATA_DIR / "logs",
    DATA_DIR / "config",
    CODE_DIR,
    CODE_DIR / "data",
    CODE_DIR / "model",
    CODE_DIR / "analysis",
    CODE_DIR / "utils",
    TESTS_DIR,
    TESTS_DIR / "unit",
    TESTS_DIR / "contract",
    DOCS_DIR,
]

# --- Environment Variable Definitions ---
# These define the keys expected in the environment.
# Defaults are provided for local development but production runs should set these explicitly.

# Model Paths
ENV_MODEL_PATH = "LLMXIVE_MODEL_PATH"
DEFAULT_MODEL_PATH = "starcoder2-3b"  # Default to local name or HuggingFace ID

# Timeouts (in seconds)
ENV_TIMEOUT_INFERENCE = "LLMXIVE_TIMEOUT_INFERENCE"
DEFAULT_TIMEOUT_INFERENCE = 120
ENV_TIMEOUT_EXECUTION = "LLMXIVE_TIMEOUT_EXECUTION"
DEFAULT_TIMEOUT_EXECUTION = 10  # Per test case as per FR-005

# Random Seeds
ENV_SEED_GLOBAL = "LLMXIVE_SEED_GLOBAL"
DEFAULT_SEED_GLOBAL = 42
ENV_SEED_DATASET = "LLMXIVE_SEED_DATASET"
DEFAULT_SEED_DATASET = 123

# Semantic Thresholds
ENV_SEMANTIC_THRESHOLD = "LLMXIVE_SEMANTIC_THRESHOLD"
DEFAULT_SEMANTIC_THRESHOLD = 0.95

# Budget Caps
ENV_BUDGET_GENERATIONS = "LLMXIVE_BUDGET_GENERATIONS"
DEFAULT_BUDGET_GENERATIONS = 1000

# --- Configuration Loading Functions ---

def _get_env_int(key: str, default: int) -> int:
    """Retrieve an integer from environment, defaulting if not set."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be an integer, got: {val}")

def _get_env_float(key: str, default: float) -> float:
    """Retrieve a float from environment, defaulting if not set."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be a float, got: {val}")

def _get_env_str(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve a string from environment, defaulting if not set."""
    val = os.getenv(key)
    if val is not None:
        return val
    return default

def get_model_path() -> str:
    """Get the path or ID for the model to load."""
    return _get_env_str(ENV_MODEL_PATH, DEFAULT_MODEL_PATH)

def get_timeout_inference() -> int:
    """Get the timeout for model inference in seconds."""
    return _get_env_int(ENV_TIMEOUT_INFERENCE, DEFAULT_TIMEOUT_INFERENCE)

def get_timeout_execution() -> int:
    """Get the timeout for code execution in seconds."""
    return _get_env_int(ENV_TIMEOUT_EXECUTION, DEFAULT_TIMEOUT_EXECUTION)

def get_seed_global() -> int:
    """Get the global random seed."""
    return _get_env_int(ENV_SEED_GLOBAL, DEFAULT_SEED_GLOBAL)

def get_seed_dataset() -> int:
    """Get the dataset sampling seed."""
    return _get_env_int(ENV_SEED_DATASET, DEFAULT_SEED_DATASET)

def get_semantic_threshold() -> float:
    """Get the semantic similarity threshold for perturbation validation."""
    return _get_env_float(ENV_SEMANTIC_THRESHOLD, DEFAULT_SEMANTIC_THRESHOLD)

def get_budget_generations() -> int:
    """Get the maximum number of generations allowed."""
    return _get_env_int(ENV_BUDGET_GENERATIONS, DEFAULT_BUDGET_GENERATIONS)

def get_config_dict() -> Dict[str, Any]:
    """
    Return a dictionary of all current configuration values loaded from environment.
    Useful for logging and debugging the current run state.
    """
    ensure_directories()
    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "code_dir": str(CODE_DIR),
        "tests_dir": str(TESTS_DIR),
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
        "model_path": get_model_path(),
        "timeout_inference": get_timeout_inference(),
        "timeout_execution": get_timeout_execution(),
        "seed_global": get_seed_global(),
        "seed_dataset": get_seed_dataset(),
        "semantic_threshold": get_semantic_threshold(),
        "budget_generations": get_budget_generations(),
    }

def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    for directory in DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> dict:
    """Return a summary of the current configuration."""
    return get_config_dict()

# Initialize directories on import if needed (or let main scripts call it)
# ensure_directories()
