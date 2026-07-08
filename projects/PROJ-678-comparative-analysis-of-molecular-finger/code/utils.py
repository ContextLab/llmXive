"""
Utility functions for the molecular fingerprint analysis pipeline.

Provides logging configuration, random seed initialization, and environment
variable loading to ensure reproducible and well-logged experiments.
"""

import logging
import os
import random
from pathlib import Path

import numpy as np

# Default seed for reproducibility as per project requirements
DEFAULT_SEED = 42

# Log file path relative to project root
LOG_FILE_PATH = "data/processed/pipeline.log"

def load_environment_variables(env_path: str | None = None) -> dict[str, str]:
    """
    Load environment variables from a .env file if it exists.

    Args:
        env_path: Path to the .env file. Defaults to looking for .env in the
                  current working directory.

    Returns:
        Dictionary of loaded environment variables (empty if file not found).
    """
    if env_path is None:
        env_path = ".env"

    env_vars = {}
    env_file = Path(env_path)

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                # Split on the first '=' only
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
                    env_vars[key] = value

    return env_vars


def init_random_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Initialize random seeds for reproducibility across libraries.

    Args:
        seed: Integer seed value. Defaults to 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Note: If using TensorFlow or PyTorch, they should be seeded in their
    # respective modules, but this covers standard Python and NumPy usage
    # required for this project's scikit-learn/RDKit workflow.


def setup_logging(
    log_level: int = logging.INFO,
    log_file: str | None = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure logging for the pipeline.

    Sets up a logger that writes to both a file (if specified) and the console.
    The logger is configured to be the root logger for the project to ensure
    consistent logging across modules.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Path to the log file. If None, no file handler is added.
                  Defaults to LOG_FILE_PATH.
        console: If True, adds a StreamHandler for console output.

    Returns:
        The configured logger instance.
    """
    if log_file is None:
        log_file = LOG_FILE_PATH

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(log_level)

    # Prevent adding multiple handlers if this function is called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File Handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """
    Retrieve a logger instance with the specified name.

    If the root logger for the pipeline has not been configured, this function
    will attempt to configure it with defaults.

    Args:
        name: Name of the logger to retrieve.

    Returns:
        Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logging()
    return logger