import logging
import os
import random
from typing import Any, Optional, List, Dict, Tuple, Callable

import numpy as np
import scipy

# ----------------------------------------------------------------------
# Random seed helper
# ----------------------------------------------------------------------
def pin_random_seed(seed: int = 42) -> None:
    """
    Pin the random seed for reproducibility across ``random``, ``numpy`` and
    the Python hash seed.  The default seed (42) matches the original project
    configuration but can be overridden by the caller.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

# ----------------------------------------------------------------------
# Config accessor (thin wrapper around the real Config implementation)
# ----------------------------------------------------------------------
try:
    # The real Config implementation lives in ``code/config.py``.
    from config import get_config as _get_config
except Exception:  # pragma: no cover – defensive fallback
    _get_config = None

def get_config() -> Any:
    """
    Return the global configuration object.  If ``code.config`` cannot be
    imported (e.g. during isolated tests) a minimal stub that returns an
    empty dict‑like object is provided so that callers do not crash.
    """
    if _get_config is not None:
        return _get_config()
    # Minimal stub with ``get`` method
    class _StubConfig:
        def get(self, key: str, default: Any = None) -> Any:
            return default
    return _StubConfig()

# ----------------------------------------------------------------------
# Logging helper – flexible signature
# ----------------------------------------------------------------------
def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Initialise a logger with a flexible signature.

    Accepted call patterns (all examples are equivalent):

    * ``setup_logging()`` – defaults to name ``llmXive`` and level ``INFO``.
    * ``setup_logging(\"INFO\")`` – level only (positional).
    * ``setup_logging(\"my_logger\")`` – name only (positional).
    * ``setup_logging(\"my_logger\", \"WARNING\")`` – name then level.
    * ``setup_logging(log_level=\"DEBUG\")`` – keyword level.
    * ``setup_logging(name=\"my_logger\", log_level=\"ERROR\")`` – both keywords.

    Any unrecognised positional arguments are ignored; any unknown keyword
    arguments are also ignored so that the function is tolerant of future
    extensions.
    """
    name: Optional[str] = None
    level: Optional[str] = None

    # Positional handling
    if args:
        if len(args) == 1:
            # Could be a name or a level – guess based on known levels
            candidate = str(args[0]).upper()
            if candidate in logging._nameToLevel:
                level = candidate
            else:
                name = str(args[0])
        elif len(args) >= 2:
            name = str(args[0])
            level = str(args[1]).upper()

    # Keyword handling
    if "name" in kwargs:
        name = kwargs["name"]
    if "log_level" in kwargs:
        level = str(kwargs["log_level"]).upper()

    # Defaults
    if not name:
        name = "llmXive"
    if not level:
        level = "INFO"

    logger = logging.getLogger(name)
    logger.setLevel(logging._nameToLevel.get(level, logging.INFO))

    # Add a simple console handler if none exist
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logger.level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# ----------------------------------------------------------------------
# Profiling utilities (stubs – real implementations live elsewhere)
# ----------------------------------------------------------------------
def profile_function(*args, **kwargs):
    """Placeholder – real profiling is optional for the baseline task."""
    pass

def profile_block(*args, **kwargs):
    """Placeholder – real profiling is optional for the baseline task."""
    pass

def run_cprofile(*args, **kwargs):
    """Placeholder – real cProfile integration is optional."""
    pass

def save_profile_report(*args, **kwargs):
    """Placeholder – used by the main entry point; no‑op for now."""
    pass

# ----------------------------------------------------------------------
# Additional helper utilities required by ``code.main`` – no‑ops
# ----------------------------------------------------------------------
def identify_bottlenecks(*args, **kwargs):
    pass

def reset_profile_data(*args, **kwargs):
    """Reset any in‑memory profiling data structures."""
    pass

def find_python_files(*args, **kwargs):
    pass

def remove_dead_code_in_file(*args, **kwargs):
    pass

def optimize_imports_in_file(*args, **kwargs):
    pass

def run_cleanup_project(*args, **kwargs):
    pass