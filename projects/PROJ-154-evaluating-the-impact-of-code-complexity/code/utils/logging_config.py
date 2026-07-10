"""
Deterministic logging configuration for scientific reproducibility.

Implements Constitution VI requirements:
- Random seed fixation for all major libraries
- Recording of library versions (specifically radon)
- Configurable logging format with timestamps and severity
"""
import os
import sys
import logging
import random
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

# Check for radon availability and version
try:
    import radon
    RADON_VERSION = radon.__version__
except ImportError:
    RADON_VERSION = "not_installed"

# Standard library versions for reproducibility tracking
LIB_VERSIONS = {
    "radon": RADON_VERSION,
    "python": sys.version,
}

def _get_run_id() -> str:
    """Generate a deterministic run ID based on timestamp and random salt."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    salt = random.randint(100000, 999999)
    return f"{timestamp}_{salt}"

def setup_deterministic_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    run_id: Optional[str] = None,
    seed: int = 42
) -> logging.Logger:
    """
    Configure the global logging environment with deterministic settings.

    Args:
        log_level: Logging severity level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional path to log file. If None, logs only to console.
        run_id: Optional explicit run ID. If None, generates one automatically.
        seed: Random seed for reproducibility (default: 42).

    Returns:
        The configured root logger instance.

    Raises:
        ValueError: If seed is not an integer.
    """
    if not isinstance(seed, int):
        raise ValueError(f"Seed must be an integer, got {type(seed)}")

    # 1. Fix random seeds for reproducibility
    random.seed(seed)
    # Note: numpy, torch, etc. will be seeded in their respective modules
    # when they are imported and used, but we set the base here.

    # 2. Configure logging format
    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s] [RunID: %(run_id)s] "
        f"[Radon: {RADON_VERSION}] - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)
    # Add 'run_id' attribute to log records
    def add_run_id(record):
        record.run_id = run_id or _get_run_id()
        return True

    formatter.converter = lambda *args: datetime.strptime(
        datetime.now().strftime(date_format), date_format
    )

    # 3. Setup handlers
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # File handler (if specified)
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # 4. Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers = []
    
    for handler in handlers:
        root_logger.addHandler(handler)

    # 5. Log initialization info
    root_logger.info("Deterministic logging configuration initialized.")
    root_logger.info(f"Random seed set to: {seed}")
    root_logger.info(f"Radon version: {RADON_VERSION}")
    root_logger.info(f"Run ID: {run_id or _get_run_id()}")
    
    # Log other library versions if available
    if "numpy" in sys.modules:
        import numpy as np
        LIB_VERSIONS["numpy"] = np.__version__
    if "torch" in sys.modules:
        import torch
        LIB_VERSIONS["torch"] = torch.__version__
    if "pandas" in sys.modules:
        import pandas as pd
        LIB_VERSIONS["pandas"] = pd.__version__
    
    version_log = ", ".join([f"{k}: {v}" for k, v in LIB_VERSIONS.items()])
    root_logger.info(f"Environment versions: {version_log}")

    return root_logger

def log_environment_info(logger: logging.Logger) -> None:
    """
    Log detailed environment information for reproducibility.
    
    Args:
        logger: The logger instance to use.
    """
    logger.info("=== Environment Information ===")
    logger.info(f"Radon Version: {RADON_VERSION}")
    logger.info(f"Python Version: {sys.version}")
    
    # Log optional dependencies if present
    optional_libs = ["numpy", "pandas", "torch", "scikit-learn", "statsmodels"]
    for lib_name in optional_libs:
        if lib_name in sys.modules:
            lib = sys.modules[lib_name]
            version = getattr(lib, "__version__", "unknown")
            logger.info(f"{lib_name} Version: {version}")
    
    logger.info("================================")

def set_seed(seed: int) -> None:
    """
    Set random seed for reproducibility across libraries.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    
    # Try to set numpy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
        
    # Try to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# Convenience function to get a logger with the configured format
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the project's deterministic configuration.
    
    Args:
        name: Optional logger name. If None, returns the root logger.
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)