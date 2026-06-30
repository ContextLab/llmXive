import logging
import os
import platform
import sys
import socket
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional, List
import json

# Global logger instance cache
_loggers: Dict[str, logging.Logger] = {}
_log_configured = False

def setup_logger(
    name: str = "benchmark",
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup and return a logger instance.
    
    Args:
        name: Logger name
        log_file: Path to log file. If None, logs to console only.
        level: Logging level
        max_bytes: Max size per log file for rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    global _log_configured
    
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    _loggers[name] = logger
    _log_configured = True
    return logger

def get_logger(name: str = "benchmark") -> logging.Logger:
    """
    Get an existing logger or create a default one if not found.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    # Fallback to default setup if logger not found
    return setup_logger(name)

def log_environment() -> None:
    """
    Log environment details including Python version, OS, CPU info, and hostname.
    This function should be called at the start of benchmark execution for reproducibility.
    """
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("ENVIRONMENT DETAILS")
    logger.info("=" * 60)
    
    # Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    logger.info(f"Python Version: {python_version}")
    logger.info(f"Python Executable: {sys.executable}")
    
    # OS Information
    logger.info(f"Operating System: {platform.system()} {platform.release()} ({platform.machine()})")
    logger.info(f"Hostname: {socket.gethostname()}")
    
    # CPU Info
    try:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        logger.info(f"CPU Count: {cpu_count}")
    except Exception:
        logger.warning("Could not determine CPU count")
    
    # Platform details
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architecture: {platform.architecture()}")
    
    # Environment variables (sensitive ones masked)
    sensitive_keys = {'PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'CREDENTIAL'}
    env_info = {}
    for key, value in os.environ.items():
        if any(s in key.upper() for s in sensitive_keys):
            env_info[key] = "***MASKED***"
        else:
            env_info[key] = value
    
    logger.info(f"Environment Variables Count: {len(env_info)}")
    logger.info("=" * 60)

def log_random_seed(seed: int) -> None:
    """
    Log the random seed used for reproducibility.
    
    Args:
        seed: The random seed integer value
    """
    logger = get_logger()
    logger.info(f"RANDOM SEED: {seed}")
    
    # Attempt to set seeds for common libraries if available
    try:
        import numpy as np
        np.random.seed(seed)
        logger.debug(f"Numpy seed set to {seed}")
    except ImportError:
        logger.debug("Numpy not available, skipping numpy seed")
    
    try:
        import random
        random.seed(seed)
        logger.debug(f"Python random seed set to {seed}")
    except ImportError:
        logger.debug("Python random not available, skipping random seed")

def log_model_versions(models: List[Dict[str, Any]]) -> None:
    """
    Log the versions and details of models being used.
    
    Args:
        models: List of dictionaries containing model information.
               Expected keys: 'model_id', 'model_type', 'version', 'source'
    """
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("MODEL VERSIONS")
    logger.info("=" * 60)
    
    if not models:
        logger.warning("No model versions provided to log")
        return
    
    for i, model in enumerate(models):
        model_id = model.get('model_id', 'unknown')
        model_type = model.get('model_type', 'unknown')
        version = model.get('version', 'unknown')
        source = model.get('source', 'unknown')
        
        logger.info(f"Model {i+1}:")
        logger.info(f"  ID: {model_id}")
        logger.info(f"  Type: {model_type}")
        logger.info(f"  Version: {version}")
        logger.info(f"  Source: {source}")
    
    logger.info("=" * 60)

def log_configuration(config: Dict[str, Any], name: str = "Configuration") -> None:
    """
    Log a configuration dictionary in a formatted way.
    
    Args:
        config: Configuration dictionary to log
        name: Name of the configuration block
    """
    logger = get_logger()
    logger.info("=" * 60)
    logger.info(f"{name.upper()}")
    logger.info("=" * 60)
    
    def log_dict(d: Dict[str, Any], indent: int = 0):
        prefix = "  " * indent
        for key, value in d.items():
            if isinstance(value, dict):
                logger.info(f"{prefix}{key}:")
                log_dict(value, indent + 1)
            elif isinstance(value, (list, tuple)):
                logger.info(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        log_dict(item, indent + 2)
                    else:
                        logger.info(f"{prefix}  - {item}")
            else:
                logger.info(f"{prefix}{key}: {value}")
    
    log_dict(config)
    logger.info("=" * 60)

def main() -> None:
    """
    Main function to demonstrate logging utilities.
    This is useful for testing the logging setup.
    """
    logger = setup_logger("demo", log_file="data/logs/demo.log")
    
    logger.info("Starting logging demonstration...")
    
    # Log environment
    log_environment()
    
    # Log a random seed
    log_random_seed(42)
    
    # Log some model versions
    models = [
        {
            'model_id': 'time-series-transformer-v1',
            'model_type': 'TimeSeries-Transformer',
            'version': '1.0.0',
            'source': 'huggingface'
        },
        {
            'model_id': 'tabpfn-base',
            'model_type': 'TabPFN',
            'version': '2.1.0',
            'source': 'huggingface'
        }
    ]
    log_model_versions(models)
    
    # Log a sample configuration
    config = {
        'datasets': ['UCI_HAR', 'DROP'],
        'seeds': [42, 123, 456],
        'timeout_per_task': 300,
        'modalities': ['time_series', 'tabular', 'text']
    }
    log_configuration(config, "Benchmark Configuration")
    
    logger.info("Logging demonstration complete.")

if __name__ == "__main__":
    main()
