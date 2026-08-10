import logging
import os
import random
import sys
from typing import Any, Callable, Iterator, List, Optional, Dict
import numpy as np

# ----------------------------------------------------------------------
# Random seed utilities
# ----------------------------------------------------------------------
def pin_random_seed(seed: int = 42) -> None:
    """
    Pin the random seed for reproducibility across the standard libraries
    that rely on randomness.

    Parameters
    ----------
    seed : int, optional
        Seed value to set for ``random``, ``numpy.random`` and the
        ``PYTHONHASHSEED`` environment variable. Default is 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

# ----------------------------------------------------------------------
# Flexible logging setup
# ----------------------------------------------------------------------
def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Initialise a logger with a flexible signature.

    Acceptable call patterns:
        setup_logging()
        setup_logging("INFO")
        setup_logging(log_level="INFO")
        setup_logging(name="my_logger")
        setup_logging("my_logger", "WARNING")
        setup_logging("my_logger", log_level="ERROR")
        setup_logging(name="my_logger", log_level="DEBUG")

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    # Default values
    name: str = "project"
    level: str = "INFO"

    # Positional handling
    if args:
        # If a single positional argument and it matches a known level, treat as level
        if len(args) == 1 and isinstance(args[0], str) and args[0].upper() in logging._nameToLevel:
            level = args[0].upper()
        else:
            # First positional is taken as name, second (if present) as level
            name = str(args[0])
            if len(args) > 1 and isinstance(args[1], str):
                level = args[1].upper()

    # Keyword handling – overrides positional if supplied
    if "name" in kwargs:
        name = kwargs["name"]
    if "log_level" in kwargs:
        level = str(kwargs["log_level"]).upper()

    logger = logging.getLogger(name)
    logger.setLevel(logging._nameToLevel.get(level, logging.INFO))

    # Ensure at least one handler exists to avoid "No handlers could be found" warnings
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# ----------------------------------------------------------------------
# Profiling utilities (place‑holders – retained for compatibility)
# ----------------------------------------------------------------------
def profile_function(func: Callable, *args, **kwargs) -> Any:
    """Placeholder profiling wrapper."""
    return func(*args, **kwargs)

def profile_block(name: str):
    """Placeholder context manager for profiling a code block."""
    class _DummyContext:
        def __enter__(self): pass
        def __exit__(self, exc_type, exc, tb): pass
    return _DummyContext()

def run_cprofile(func: Callable, *args, **kwargs) -> Any:
    """Run a function under cProfile – simplified version."""
    return func(*args, **kwargs)

def save_profile_report(data: Any, path: str) -> None:
    """Placeholder for saving profiling reports."""
    with open(path, "w") as f:
        f.write(str(data))

def identify_bottlenecks(profile_data: Any) -> List[str]:
    """Placeholder for bottleneck identification."""
    return []

def reset_profile_data() -> None:
    """Placeholder to reset profiling state."""
    pass

# Additional utility functions that were previously present remain untouched.