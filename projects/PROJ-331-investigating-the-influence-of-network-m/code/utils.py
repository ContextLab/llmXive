import logging
import os
import json
import hashlib
import time
import platform
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable
import functools
import traceback
import importlib.metadata

# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataNotFoundError(PipelineError):
    """Raised when required data files are missing."""
    pass

class ProcessingError(PipelineError):
    """Raised when a processing step fails."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration is invalid."""
    pass

# Logger Setup
_logger_instance: Optional[logging.Logger] = None
_log_initialized: bool = False

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Returns a configured logger instance that writes to both console and file.
    The file is always `data/logs/pipeline.log` relative to the project root.
    Ensures single initialization to prevent duplicate handlers.
    """
    global _logger_instance, _log_initialized
    if not _log_initialized:
        _logger_instance = logging.getLogger(name)
        _logger_instance.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers if called multiple times
        if not _logger_instance.handlers:
            # Console Handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(ch_format)
            _logger_instance.addHandler(ch)

            # File Handler (Absolute path resolution to ensure it lands in data/logs)
            # We assume the script is run from the project root or we resolve relative to __file__
            log_dir = Path(__file__).parent.parent / "data" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "pipeline.log"

            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(fh_format)
            _logger_instance.addHandler(fh)
        
        _log_initialized = True
    return _logger_instance

def log_error(e: Exception, context: str = "") -> None:
    """Logs an exception with traceback context."""
    logger = get_logger()
    logger.error(f"{context}: {str(e)}", exc_info=True)

def log_execution_time(func: Callable) -> Callable:
    """Decorator to log execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end = time.time()
            logger = get_logger()
            logger.info(f"Function {func.__name__} executed in {end - start:.4f} seconds")
    return wrapper

# Directory & File Utilities
def safe_mkdir(path: Union[str, Path]) -> Path:
    """Creates a directory if it doesn't exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def safe_write_text(path: Union[str, Path], content: str, encoding: str = "utf-8") -> Path:
    """Writes text to a file, creating parent directories if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)
    return p

def safe_read_text(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Reads text from a file."""
    return Path(path).read_text(encoding=encoding)

def safe_write_json(path: Union[str, Path], data: Any, indent: int = 2) -> Path:
    """Writes JSON to a file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)
    return p

def safe_read_json(path: Union[str, Path]) -> Any:
    """Reads JSON from a file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Numpy Utilities
def save_npy(path: Union[str, Path], array: Any) -> Path:
    """Saves a numpy array to .npy format."""
    import numpy as np
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(p, array)
    return p

def load_npy(path: Union[str, Path]) -> Any:
    """Loads a numpy array from .npy format."""
    import numpy as np
    return np.load(path)

# Hashing Utilities
def compute_sha256(file_path: Union[str, Path]) -> str:
    """Computes the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# Statistical Logging & Validation (Constitution Principle VII)
def log_statistical_parameters(
    bonferroni_alpha: float,
    seed: int,
    permutation_count: int,
    vif_threshold: float,
    additional_params: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs all required statistical parameters to the pipeline log as per FR-008
    and Constitution Principle VII.
    
    Args:
        bonferroni_alpha: The Bonferroni-adjusted alpha level.
        seed: The random seed used for reproducibility.
        permutation_count: Number of permutations used in tests.
        vif_threshold: The VIF threshold for multicollinearity check.
        additional_params: Optional dict of other parameters to log.
    """
    logger = get_logger()
    
    # Log critical parameters explicitly
    logger.info("=" * 60)
    logger.info("STATISTICAL CONFIGURATION (Constitution Principle VII)")
    logger.info("=" * 60)
    logger.info(f"Bonferroni Alpha: {bonferroni_alpha}")
    logger.info(f"Random Seed: {seed}")
    logger.info(f"Permutation Count: {permutation_count}")
    logger.info(f"VIF Threshold: {vif_threshold}")
    
    # Log library versions
    logger.info("-" * 40)
    logger.info("Library Versions:")
    libs_to_check = ['numpy', 'scipy', 'pandas', 'networkx', 'statsmodels', 'nibabel']
    for lib_name in libs_to_check:
        try:
            version = importlib.metadata.version(lib_name)
            logger.info(f"  {lib_name}: {version}")
        except importlib.metadata.PackageNotFoundError:
            logger.warning(f"  {lib_name}: Not installed")
    
    # Log system info
    logger.info("-" * 40)
    logger.info(f"System: {platform.system()} {platform.release()}")
    logger.info(f"Python: {sys.version}")
    logger.info("=" * 60)
    
    if additional_params:
        logger.info("Additional Parameters:")
        for key, value in additional_params.items():
            logger.info(f"  {key}: {value}")

def validate_statistical_logging(log_path: Union[str, Path]) -> bool:
    """
    Verifies that the pipeline log contains all required statistical parameters
    as per Constitution Principle VII.
    
    Args:
        log_path: Path to the pipeline.log file.
        
    Returns:
        True if all required parameters are found, False otherwise.
        
    Raises:
        ConfigurationError: If required parameters are missing.
    """
    log_path = Path(log_path)
    if not log_path.exists():
        raise ConfigurationError(f"Log file not found: {log_path}")
    
    content = log_path.read_text()
    
    required_markers = [
        "Bonferroni Alpha:",
        "Random Seed:",
        "Permutation Count:",
        "VIF Threshold:",
        "Library Versions:"
    ]
    
    missing = []
    for marker in required_markers:
        if marker not in content:
            missing.append(marker)
    
    if missing:
        raise ConfigurationError(
            f"Statistical logging validation failed. Missing markers: {', '.join(missing)}"
        )
    
    return True

def log_execution_context(step_name: str, status: str = "STARTED", details: Optional[str] = None) -> None:
    """
    Logs the execution context of a pipeline step.
    
    Args:
        step_name: Name of the step being executed.
        status: Status of the step (STARTED, COMPLETED, FAILED, SKIPPED).
        details: Optional details about the step.
    """
    logger = get_logger()
    msg = f"[{status}] Step: {step_name}"
    if details:
        msg += f" - {details}"
    if status == "FAILED":
        logger.error(msg)
    elif status == "COMPLETED":
        logger.info(msg)
    else:
        logger.info(msg)
