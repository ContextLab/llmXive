"""
Shared utilities for the project.
Provides logging, configuration loading, path resolution, and retry logic.
"""
import logging
import os
import time
from pathlib import Path
from typing import Optional, Callable, Any, Dict
import random

# Logger cache to avoid re-creating loggers
_loggers: Dict[str, logging.Logger] = {}

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configures the root logger with a console handler and optional file handler.
    """
    if not _loggers:  # Only setup once
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File Handler (if specified)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves or creates a logger with the given name.
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
        # Ensure it doesn't propagate to root if root is already configured elsewhere
        # but usually we want propagation to the root handler we set up.
        _loggers[name].propagate = True
    return _loggers[name]

def load_config_env(env_file: Optional[str] = None) -> Dict[str, str]:
    """
    Loads environment variables from a .env file if it exists.
    Returns a dictionary of loaded variables.
    """
    config = {}
    if env_file and os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
                        os.environ[key.strip()] = value.strip()
    return config

def get_project_paths() -> Dict[str, Path]:
    """
    Returns a dictionary of key project paths relative to the project root.
    Assumes the script is run from the project root or code/ directory.
    """
    # Determine project root: if __file__ is in code/, go up one level.
    # If run as a module, we might need a different strategy, but for scripts:
    current_file = Path(__file__).resolve()
    # If this file is in code/, parent is root.
    if current_file.name == 'utils.py' and current_file.parent.name == 'code':
        root = current_file.parent
    else:
        # Fallback: assume current working directory is root
        root = Path.cwd()

    return {
        "root": root,
        "code": root / "code",
        "data_raw": root / "data" / "raw",
        "data_processed": root / "data" / "processed",
        "data_reports": root / "data" / "reports",
        "tests": root / "tests",
        "state": root / "state",
        "state_projects": root / "state" / "projects",
    }

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    jitter: bool = True
) -> Any:
    """
    Executes a function with exponential backoff and jitter on failure.
    Retries up to max_retries times.
    """
    attempt = 0
    delay = base_delay

    while attempt < max_retries:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                raise e

            # Calculate delay with jitter
            if jitter:
                delay = min(max_delay, delay * (2 ** random.random()))
            else:
                delay = min(max_delay, delay * 2)

            logging.getLogger(__name__).warning(
                f"Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay:.2f}s..."
            )
            time.sleep(delay)

    # Should not reach here due to the raise in the loop
    raise RuntimeError("Retry logic failed unexpectedly")
