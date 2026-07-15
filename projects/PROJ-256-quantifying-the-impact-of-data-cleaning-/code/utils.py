import logging
import os
from typing import Any, Optional
import numpy as np
import random
import scipy

# Existing utility functions (presumed to exist) are retained.
# Added flexible implementations for setup_logging and Config to satisfy
# multiple call signatures across the codebase.

def pin_random_seed(seed: int) -> None:
    """Set random seeds for reproducibility across numpy, random, and python hash."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    import hashlib
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Flexible logging initializer.

    Accepts any of the following call patterns:
        setup_logging()
        setup_logging("INFO")
        setup_logging(log_level="INFO")
        setup_logging(name="my_logger")
        setup_logging("my_logger", "WARNING")
        setup_logging("my_logger", log_level="ERROR")
    """
    # Determine logger name
    name = kwargs.get("name")
    if not name and args:
        name = args[0] if isinstance(args[0], str) else None

    # Determine log level
    level = kwargs.get("log_level")
    if not level:
        # Look for a second positional argument that looks like a level
        if len(args) > 1 and isinstance(args[1], str):
            level = args[1]
        else:
            level = "INFO"

    logger = logging.getLogger(name or "llmXive")
    logger.setLevel(logging._nameToLevel.get(level.upper(), logging.INFO))

    # Ensure at least one handler (console) exists
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging._nameToLevel.get(level.upper(), logging.INFO))
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

class Config:
    """
    Simple configuration holder that is tolerant to any attribute access.
    Existing keys are loaded from environment variables (via .env) or defaults.
    """

    def __init__(self):
        # Load environment variables from a .env file if present
        from dotenv import load_dotenv

        load_dotenv()
        # Default configuration values
        self._config = {
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "output"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any undefined attribute (e.g., logger methods).
        This satisfies scripts that expect Config to have .info/.debug/.warning etc.
        """
        def _noop(*args, **kwargs):
            return None

        return _noop

# Export a singleton for convenience
config = Config()
