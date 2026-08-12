import hashlib
import logging
import os
import random
import sys
import time
from typing import Any, Callable, Dict, List, Optional

# ------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------

def compute_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified hash algorithm.
    Default is SHA-256.
    """
    h = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def pin_random_seed(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility across ``random``, ``numpy`` and
    ``torch`` (if available). This function is deliberately tolerant of
    missing optional dependencies.
    """
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass

# ------------------------------------------------------------
# Flexible Logging Setup
# ------------------------------------------------------------
def setup_logging(*args, **kwargs) -> logging.Logger:
    """
    Initialise a logger. Accepts a wide variety of call signatures to remain
    compatible with legacy scripts.

    Supported patterns:
    - setup_logging()
    - setup_logging("INFO")
    - setup_logging(log_level="DEBUG")
    - setup_logging(name="my_logger")
    - setup_logging("my_logger", "WARNING")
    - setup_logging("my_logger", log_level="ERROR")
    - setup_logging(name="my_logger", log_level="INFO")
    """
    # Resolve positional arguments
    name: Optional[str] = None
    level: Optional[str] = None

    if len(args) == 1:
        # Could be name or level
        if isinstance(args[0], str) and args[0].upper() in logging._nameToLevel:
            level = args[0].upper()
        else:
            name = args[0]
    elif len(args) >= 2:
        name, level = args[0], args[1]

    # Resolve keyword arguments
    if "name" in kwargs:
        name = kwargs["name"]
    if "log_level" in kwargs:
        level = kwargs["log_level"]
    if "level" in kwargs:
        level = kwargs["level"]

    # Defaults
    if name is None:
        name = __name__
    if level is None:
        level = "INFO"

    logger = logging.getLogger(name)
    logger.setLevel(logging._nameToLevel.get(level.upper(), logging.INFO))

    # Ensure at least one handler exists
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# ------------------------------------------------------------
# Simple profiling utilities (no‑op placeholders)
# ------------------------------------------------------------
_profile_data: List[Dict[str, Any]] = []

def profile_function(func: Callable) -> Callable:
    """Decorator that records execution time; placeholder implementation."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        _profile_data.append(
            {"function": func.__name__, "duration_seconds": duration, "status": "success"}
        )
        return result
    return wrapper

def profile_block(name: str):
    """Context manager for profiling a code block; placeholder implementation."""
    class _Profiler:
        def __enter__(self):
            self.start = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start
            _profile_data.append(
                {
                    "block": name,
                    "duration_seconds": duration,
                    "status": "error" if exc_type else "success",
                }
            )
    return _Profiler()

def run_cprofile(output_file: str = "cprofile.prof") -> None:
    """Run cProfile on the whole process; placeholder does nothing."""
    logger = setup_logging()
    logger.debug("cProfile placeholder invoked; no profiling performed.")

def save_profile_report(report_path: str = "profile_report.json") -> None:
    """Write the collected profiling data to a JSON file."""
    logger = setup_logging()
    logger.debug(f"Saving profiling report to {report_path}")
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(_profile_data, f, indent=2, default=str)

def identify_bottlenecks(threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
    """Return profiling entries exceeding the threshold."""
    return [entry for entry in _profile_data if entry.get("duration_seconds", 0) > threshold_seconds]

def reset_profile_data() -> None:
    """Clear the in‑memory profiling buffer."""
    _profile_data.clear()

# ------------------------------------------------------------
# End of utils.py
# ------------------------------------------------------------
