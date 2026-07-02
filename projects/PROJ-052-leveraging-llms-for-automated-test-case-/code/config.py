"""
Configuration module for the LLM test generation pipeline.

Loads environment variables for sample limits, timeouts, model paths,
and enforces a runtime limit to comply with the 6-hour wall-clock budget.
"""
import os
import sys
import time
from typing import Optional
from pathlib import Path

# Default paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = "models/phi-2-q4_k_m.gguf"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data"
DEFAULT_LOGS_DIR = PROJECT_ROOT / "logs"

# Environment variable keys
ENV_MODEL_PATH = "LLM_MODEL_PATH"
ENV_DATA_DIR = "DATA_DIR"
ENV_OUTPUT_DIR = "OUTPUT_DIR"
ENV_LOGS_DIR = "LOGS_DIR"
ENV_SAMPLE_LIMIT = "SAMPLE_LIMIT"
ENV_TIMEOUT_COMPILE = "TIMEOUT_COMPILE_SECONDS"
ENV_TIMEOUT_EXEC = "TIMEOUT_EXEC_SECONDS"
ENV_TIMEOUT_INFERENCE = "TIMEOUT_INFERENCE_SECONDS"
ENV_RUNTIME_LIMIT = "RUNTIME_LIMIT_SECONDS"

# Default values
DEFAULT_SAMPLE_LIMIT = 100
DEFAULT_TIMEOUT_COMPILE = 120
DEFAULT_TIMEOUT_EXEC = 60
DEFAULT_TIMEOUT_INFERENCE = 300
DEFAULT_RUNTIME_LIMIT = 21600  # 6 hours in seconds

# Global state for runtime tracking
_start_time: Optional[float] = None


def init_runtime_tracker() -> None:
    """Initialize the runtime tracker. Must be called at the start of main."""
    global _start_time
    _start_time = time.time()


def check_runtime_limit() -> None:
    """
    Check if the cumulative execution time has exceeded the configured limit.
    Raises RuntimeError if the limit is exceeded.
    """
    if _start_time is None:
        # If not initialized, assume no limit check needed or initialize now
        _start_time = time.time()
        return

    elapsed = time.time() - _start_time
    limit = get_runtime_limit()

    if elapsed > limit:
        raise RuntimeError(
            f"Runtime limit exceeded: {elapsed:.2f}s > {limit}s. "
            "Stopping execution to comply with budget constraints."
        )


def get_sample_limit() -> int:
    """Get the maximum number of samples to process."""
    return int(os.getenv(ENV_SAMPLE_LIMIT, DEFAULT_SAMPLE_LIMIT))


def get_timeout_compile() -> int:
    """Get the timeout for Java compilation in seconds."""
    return int(os.getenv(ENV_TIMEOUT_COMPILE, DEFAULT_TIMEOUT_COMPILE))


def get_timeout_exec() -> int:
    """Get the timeout for test execution in seconds."""
    return int(os.getenv(ENV_TIMEOUT_EXEC, DEFAULT_TIMEOUT_EXEC))


def get_timeout_inference() -> int:
    """Get the timeout for LLM inference in seconds."""
    return int(os.getenv(ENV_TIMEOUT_INFERENCE, DEFAULT_TIMEOUT_INFERENCE))


def get_runtime_limit() -> int:
    """Get the total allowed runtime in seconds."""
    return int(os.getenv(ENV_RUNTIME_LIMIT, DEFAULT_RUNTIME_LIMIT))


def get_model_path() -> Path:
    """Get the path to the LLM model file."""
    path_str = os.getenv(ENV_MODEL_PATH, DEFAULT_MODEL_PATH)
    return Path(path_str)


def get_data_dir() -> Path:
    """Get the data directory path."""
    path_str = os.getenv(ENV_DATA_DIR, str(DEFAULT_DATA_DIR))
    return Path(path_str)


def get_output_dir() -> Path:
    """Get the output directory path."""
    path_str = os.getenv(ENV_OUTPUT_DIR, str(DEFAULT_OUTPUT_DIR))
    return Path(path_str)


def get_logs_dir() -> Path:
    """Get the logs directory path."""
    path_str = os.getenv(ENV_LOGS_DIR, str(DEFAULT_LOGS_DIR))
    return Path(path_str)


def ensure_directories() -> None:
    """Create necessary directories if they don't exist."""
    for dir_path in [get_data_dir(), get_output_dir(), get_logs_dir()]:
        dir_path.mkdir(parents=True, exist_ok=True)