"""
Logging infrastructure for the compiler optimization impact study.
Provides specialized loggers and handlers for compiler versions, flags,
execution warnings, and stability failures (NaN detection).
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Constants for log paths
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize the logging infrastructure.
    
    Args:
        log_level: Logging severity threshold.
        log_file: Optional path to a log file. Defaults to data/logs/run_<timestamp>.log.
    
    Returns:
        The configured logger instance.
    """
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("compiler_opt_bench")
    _logger.setLevel(log_level)
    _logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = str(LOG_DIR / f"run_{timestamp}.log")
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    _logger.addHandler(file_handler)

    _logger.info(f"Logging initialized. Output file: {log_file}")
    return _logger

def get_logger() -> logging.Logger:
    """Get the global logger instance, initializing if necessary."""
    if _logger is None:
        return setup_logging()
    return _logger

def log_compiler_version(compiler: str, version: str, flags: List[str]) -> None:
    """
    Log compiler identification and configuration details.
    
    Args:
        compiler: Compiler name (e.g., 'g++', 'clang++').
        version: Compiler version string.
        flags: List of optimization flags used.
    """
    logger = get_logger()
    log_entry = {
        "event": "compiler_version",
        "timestamp": datetime.now().isoformat(),
        "compiler": compiler,
        "version": version,
        "flags": flags,
        "log_level": "INFO"
    }
    logger.info(json.dumps(log_entry))

def log_flag_combination(config_id: str, flags: List[str], tensor_dim: str) -> None:
    """
    Log a specific flag combination being tested.
    
    Args:
        config_id: Unique identifier for the configuration.
        flags: List of flags.
        tensor_dim: Tensor dimension (e.g., '768x768').
    """
    logger = get_logger()
    log_entry = {
        "event": "flag_combination",
        "timestamp": datetime.now().isoformat(),
        "config_id": config_id,
        "flags": flags,
        "tensor_dimension": tensor_dim,
        "log_level": "INFO"
    }
    logger.info(json.dumps(log_entry))

def log_execution_warning(warning_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log runtime execution warnings (e.g., memory pressure, timeouts).
    
    Args:
        warning_type: Type of warning (e.g., 'Memory Pressure', 'Timeout').
        message: Human-readable warning message.
        details: Optional dictionary of additional context.
    """
    logger = get_logger()
    log_entry = {
        "event": "execution_warning",
        "timestamp": datetime.now().isoformat(),
        "warning_type": warning_type,
        "message": message,
        "details": details or {},
        "log_level": "WARNING"
    }
    logger.warning(json.dumps(log_entry))

def log_nan_detection(config_id: str, kernel_type: str, tensor_dim: str) -> None:
    """
    Log detection of NaN values in output tensors.
    
    Args:
        config_id: Configuration ID that produced NaN.
        kernel_type: Kernel type (e.g., 'matmul', 'softmax').
        tensor_dim: Tensor dimension.
    """
    logger = get_logger()
    log_entry = {
        "event": "nan_detection",
        "timestamp": datetime.now().isoformat(),
        "config_id": config_id,
        "kernel_type": kernel_type,
        "tensor_dimension": tensor_dim,
        "log_level": "ERROR"
    }
    logger.error(json.dumps(log_entry))

def log_stability_failure(config_id: str, kernel_type: str, error_metric: float, threshold: float) -> None:
    """
    Log a stability failure where error exceeds the threshold.
    
    Args:
        config_id: Configuration ID.
        kernel_type: Kernel type.
        error_metric: Calculated error value (e.g., L2 relative error).
        threshold: Threshold that was exceeded.
    """
    logger = get_logger()
    log_entry = {
        "event": "stability_failure",
        "timestamp": datetime.now().isoformat(),
        "config_id": config_id,
        "kernel_type": kernel_type,
        "error_metric": error_metric,
        "threshold": threshold,
        "status": "UNSTABLE",
        "log_level": "ERROR"
    }
    logger.error(json.dumps(log_entry))

def main() -> None:
    """
    CLI entry point to test logging functionality.
    Runs a series of log calls to verify the infrastructure.
    """
    setup_logging()
    logger = get_logger()
    
    logger.info("Testing logging infrastructure...")
    log_compiler_version("g++", "11.4.0", ["-O2", "-march=native"])
    log_flag_combination("cfg_001", ["-O3", "-ffast-math"], "512x512")
    log_execution_warning("Memory Pressure", "Allocations exceeded 80% RAM, downscaling requested", {"original": "768x768", "scaled": "512x512"})
    log_nan_detection("cfg_002", "softmax", "1024x1024")
    log_stability_failure("cfg_003", "matmul", 1.5e-4, 1e-5)
    logger.info("Logging test complete.")

if __name__ == "__main__":
    main()
