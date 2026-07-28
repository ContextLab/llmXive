import logging
import os
import time
from pathlib import Path
from typing import Optional, Callable, Any, Dict
import random

# Global logger configuration state
_logger_configured = False

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure root logger with console and optional file handlers.
    """
    global _logger_configured
    if _logger_configured:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)

    _logger_configured = True

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    """
    return logging.getLogger(name)

def load_config_env(env_file: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file if it exists.
    """
    config = {}
    if env_file and os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    config[key.strip()] = value.strip()
    return config

def get_project_paths() -> Dict[str, Path]:
    """
    Return a dictionary of project root paths based on the current working directory.
    Assumes the script is run from the project root.
    """
    root = Path.cwd()
    # Fallback if run from inside code/
    if (root / "code").exists() and (root / "data").exists():
        pass
    elif (root.parent / "code").exists() and (root.parent / "data").exists():
        root = root.parent

    return {
        "root": root,
        "code": root / "code",
        "data_raw": root / "data" / "raw",
        "data_processed": root / "data" / "processed",
        "data_reports": root / "data" / "reports",
        "tests": root / "tests",
        "state": root / "state"
    }

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    logger: Optional[logging.Logger] = None
) -> Any:
    """
    Execute a function with exponential backoff retry logic.
    """
    if logger is None:
        logger = get_logger(__name__)
    
    attempt = 0
    delay = base_delay
    
    while attempt < max_retries:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                raise
            
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)
            delay = min(delay * 2, max_delay) + random.uniform(0, 0.1)
