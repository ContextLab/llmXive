import logging
import os
import random
from typing import Any, Optional, List, Dict, Tuple, Callable
import numpy as np
import scipy
import hashlib
from pathlib import Path
import cProfile
import pstats
import time
import sys
import importlib.util

# --- Random Seed Pinning ---
def pin_random_seed(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility across numpy, random, and scipy.
    """
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(scipy, 'random'):
        scipy.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

# --- File Checksum ---
def compute_file_checksum(filepath: str) -> str:
    """
    Compute SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# --- Logging Setup ---
def setup_logging(log_level: Optional[str] = "INFO", name: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    Handles multiple call signatures:
      - setup_logging()
      - setup_logging("INFO")
      - setup_logging(log_level="INFO")
      - setup_logging("my_logger")
      - setup_logging("my_logger", "WARNING")
      - setup_logging("my_logger", log_level="ERROR")
    """
    # Determine log_level and name based on arguments
    final_level = log_level
    final_name = name

    # Heuristic: if name is None and log_level is a string:
    if name is None and isinstance(log_level, str):
        # Check if it's a valid level
        if log_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            final_level = log_level.upper()
            final_name = None
        else:
            final_name = log_level
            final_level = "INFO" # default level if name provided

    # Handle positional args if passed as *args (not in this signature, but for robustness)
    # The signature here is fixed, but we handle the cases described in the prompt
    # by interpreting the first arg as level or name.

    # If we are called as setup_logging("my_logger", "WARNING"), the signature above
    # would map "my_logger" to log_level and "WARNING" to name?
    # No, the signature is setup_logging(log_level: Optional[str] = "INFO", name: Optional[str] = None)
    # So if called as setup_logging("my_logger", "WARNING"), log_level="my_logger", name="WARNING"
    # Then we detect: log_level is not a valid level, so it's a name. name is "WARNING" (level).
    if name is not None and isinstance(name, str):
        if name.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            # name was actually a level
            final_level = name.upper()
            final_name = log_level if isinstance(log_level, str) and log_level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] else None
        elif final_name is None:
            final_name = name
            # If log_level was a level, keep it. If it was a name, we have a conflict.
            # But if log_level was a level, we are good.
            # If log_level was a name (and name is also a name?), we prefer the second as level?
            # The prompt says: setup_logging("my_logger", "WARNING") -> name then level.
            # So log_level="my_logger" (treated as name), name="WARNING" (treated as level).
            if isinstance(log_level, str) and log_level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                final_name = log_level
                final_level = name.upper()

    # Configure logger
    logger = logging.getLogger(final_name)
    if logger.handlers:
        return logger # Already configured

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    try:
        logger.setLevel(final_level)
    except ValueError:
        logger.setLevel(logging.INFO)

    logger.propagate = False
    return logger

# --- Config Helper ---
def get_config(key: str, default: Any = None) -> Any:
    """
    Mock config getter for compatibility with scripts calling config.get().
    In a real scenario, this would read from env vars or a config file.
    """
    # Fallback to environment variables
    val = os.getenv(key)
    if val is not None:
        return val
    return default

# --- Profiling Utilities (Merged from profiler.py) ---
_profile_data: List[Dict[str, Any]] = []

def profile_function(func: Callable) -> Callable:
    """Decorator to profile a function."""
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            status = "success"
        except Exception as e:
            status = "failed"
            raise
        finally:
            duration = time.time() - start
            _profile_data.append({
                "function": func.__name__,
                "duration_seconds": duration,
                "status": status
            })
        return result
    return wrapper

def profile_block(name: str = "block"):
    """Context manager to profile a block of code."""
    class ProfilerBlock:
        def __enter__(self):
            self.start = time.time()
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start
            _profile_data.append({
                "block": name,
                "duration_seconds": duration,
                "status": "success" if exc_type is None else "failed"
            })
    return ProfilerBlock()

def run_cprofile(target_func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Run cProfile on a function and return stats."""
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        result = target_func(*args, **kwargs)
    finally:
        profiler.disable()
    stats = pstats.Stats(profiler)
    # Convert to serializable dict (simplified)
    return {
        "total_calls": stats.total_calls,
        "total_time": stats.total_tt,
        "top_functions": [
            (func, (cc, nc, tt, ct, callers))
            for func, (cc, nc, tt, ct, callers) in sorted(stats.stats.items(), key=lambda x: x[1][3], reverse=True)[:10]
        ]
    }

def save_profile_report(output_path: str = "output/profile_report.txt") -> None:
    """Save profile data to a file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("Profile Report\n")
        f.write("=" * 40 + "\n")
        for item in _profile_data:
            f.write(f"{'block' if 'block' in item else 'function'}: {item.get('block') or item.get('function')}\n")
            f.write(f"  Duration: {item.get('duration_seconds', 0):.4f}s\n")
            f.write(f"  Status: {item.get('status', 'unknown')}\n")
        f.write("\nSummary:\n")
        f.write(f"  Total successful: {sum(1 for item in _profile_data if item.get('status') == 'success')}\n")
        f.write(f"  Total failed: {sum(1 for item in _profile_data if item.get('status') == 'failed')}\n")

def identify_bottlenecks(threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
    """Identify functions/blocks taking longer than threshold."""
    return [item for item in _profile_data if item.get("duration_seconds", 0) > threshold_seconds]

def reset_profile_data() -> None:
    """Clear profile data."""
    global _profile_data
    _profile_data = []

# --- Cleanup Utilities (Merged from cleanup_utils.py) ---
def find_python_files(directory: str) -> List[Path]:
    """Find all .py files in a directory recursively."""
    return list(Path(directory).rglob("*.py"))

def remove_dead_code_in_file(filepath: Path) -> bool:
    """
    Placeholder for dead code removal logic.
    Currently just logs that it was called.
    """
    logger = setup_logging("INFO", "CleanupUtils")
    logger.info(f"Scanning {filepath} for dead code (placeholder logic).")
    return True

def optimize_imports_in_file(filepath: Path) -> bool:
    """
    Placeholder for import optimization logic.
    Currently just logs that it was called.
    """
    logger = setup_logging("INFO", "CleanupUtils")
    logger.info(f"Optimizing imports in {filepath} (placeholder logic).")
    return True

def run_cleanup_project(directory: str = "code") -> None:
    """Run cleanup utilities on a directory."""
    logger = setup_logging("INFO", "CleanupUtils")
    logger.info(f"Running cleanup on {directory}")
    files = find_python_files(directory)
    for f in files:
        remove_dead_code_in_file(f)
        optimize_imports_in_file(f)
    logger.info("Cleanup complete.")
