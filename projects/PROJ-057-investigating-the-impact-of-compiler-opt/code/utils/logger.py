"""
Logging infrastructure for the compiler optimization impact study.

This module provides a centralized logging system to record:
- Compiler versions (GCC, Clang)
- Flag combinations used in experiments
- Runtime warnings (NaN detection, memory pressure, stability failures)

All logs are written to both console and file with structured JSON formatting
for downstream analysis.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


# Global logger instance
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None


def _ensure_log_directory() -> Path:
    """Ensure the log directory exists."""
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _get_log_filename() -> str:
    """Generate a timestamped log filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"experiment_{timestamp}.log"


def _create_json_formatter() -> logging.Formatter:
    """Create a custom JSON formatter for structured logging."""
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "module": record.module,
                "message": record.getMessage(),
            }
            # Add extra fields if present
            if hasattr(record, 'compiler_version'):
                log_obj['compiler_version'] = record.compiler_version
            if hasattr(record, 'flag_combination'):
                log_obj['flag_combination'] = record.flag_combination
            if hasattr(record, 'warning_type'):
                log_obj['warning_type'] = record.warning_type
            if hasattr(record, 'config_id'):
                log_obj['config_id'] = record.config_id
            if hasattr(record, 'kernel'):
                log_obj['kernel'] = record.kernel
            if hasattr(record, 'tensor_dim'):
                log_obj['tensor_dim'] = record.tensor_dim
            if hasattr(record, 'error_metric'):
                log_obj['error_metric'] = record.error_metric
            if hasattr(record, 'threshold'):
                log_obj['threshold'] = record.threshold
            if hasattr(record, 'details'):
                log_obj['details'] = record.details
            
            return json.dumps(log_obj)
    
    return JsonFormatter()


def setup_logging(
    log_level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Setup the centralized logging infrastructure.
    
    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG)
        log_to_file: Whether to write logs to a file
        log_dir: Optional custom log directory (defaults to data/logs)
    
    Returns:
        The configured logger instance
    
    Side Effects:
        - Creates log directory if needed
        - Sets up file and console handlers
        - Stores global logger reference
    """
    global _logger, _log_file_path
    
    if _logger is not None:
        return _logger
    
    # Create logger
    _logger = logging.getLogger("compiler_opt_benchmark")
    _logger.setLevel(log_level)
    
    # Clear any existing handlers
    _logger.handlers.clear()
    
    # Create formatter
    formatter = _create_json_formatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        if log_dir is None:
            log_dir = _ensure_log_directory()
        else:
            log_dir.mkdir(parents=True, exist_ok=True)
        
        log_filename = _get_log_filename()
        _log_file_path = log_dir / log_filename
        
        file_handler = logging.FileHandler(_log_file_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    
    return _logger


def get_logger() -> logging.Logger:
    """
    Get the global logger instance.
    
    Raises:
        RuntimeError: If logging has not been initialized via setup_logging()
    """
    if _logger is None:
        raise RuntimeError("Logging not initialized. Call setup_logging() first.")
    return _logger


def log_compiler_version(compiler: str, version: str, flags: List[str]) -> None:
    """
    Log compiler version information.
    
    Args:
        compiler: Compiler name (e.g., 'gcc', 'clang')
        version: Compiler version string
        flags: List of optimization flags used
    
    Example:
        log_compiler_version("gcc", "11.4.0", ["-O2", "-march=native"])
    """
    logger = get_logger()
    logger.info(
        f"Compiler detected: {compiler} {version}",
        extra={
            'compiler_version': f"{compiler} {version}",
            'flag_combination': flags
        }
    )


def log_flag_combination(config_id: str, flags: List[str], kernel: str) -> None:
    """
    Log a flag combination being tested.
    
    Args:
        config_id: Unique identifier for this configuration
        flags: List of optimization flags
        kernel: Kernel type being compiled (e.g., 'matmul', 'softmax')
    
    Example:
        log_flag_combination("cfg_001", ["-O3", "-ffast-math"], "matmul")
    """
    logger = get_logger()
    logger.info(
        f"Testing configuration {config_id} with flags: {flags} for {kernel}",
        extra={
            'config_id': config_id,
            'flag_combination': flags,
            'kernel': kernel
        }
    )


def log_execution_warning(
    warning_type: str,
    message: str,
    config_id: Optional[str] = None,
    kernel: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a runtime warning during execution.
    
    Args:
        warning_type: Type of warning (e.g., 'Memory Pressure', 'Timeout', 'Compilation Error')
        message: Human-readable warning message
        config_id: Optional configuration ID
        kernel: Optional kernel name
        details: Optional dictionary of additional details
    
    Example:
        log_execution_warning("Memory Pressure", "Allocation failed, downsampling...", 
                            config_id="cfg_001", kernel="matmul")
    """
    logger = get_logger()
    extra = {
        'warning_type': warning_type,
        'message': message,
    }
    if config_id:
        extra['config_id'] = config_id
    if kernel:
        extra['kernel'] = kernel
    if details:
        extra['details'] = details
    
    logger.warning(message, extra=extra)


def log_nan_detection(
    config_id: str,
    kernel: str,
    tensor_dim: str,
    flags: List[str],
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log NaN detection in output tensors.
    
    Args:
        config_id: Configuration ID that produced NaN
        kernel: Kernel type
        tensor_dim: Tensor dimensions (e.g., "512x512")
        flags: Optimization flags used
        details: Optional additional details
    
    Example:
        log_nan_detection("cfg_003", "matmul", "768x768", ["-O3", "-ffast-math"])
    """
    logger = get_logger()
    logger.warning(
        f"NaN detected in {kernel} output for config {config_id}",
        extra={
            'warning_type': 'NaN Detection',
            'config_id': config_id,
            'kernel': kernel,
            'tensor_dim': tensor_dim,
            'flag_combination': flags,
            'details': details
        }
    )


def log_stability_failure(
    config_id: str,
    kernel: str,
    l2_error: float,
    max_diff: float,
    threshold: float,
    flags: List[str]
) -> None:
    """
    Log a numerical stability failure.
    
    Args:
        config_id: Configuration ID
        kernel: Kernel type
        l2_error: Calculated L2 relative error
        max_diff: Maximum absolute difference
        threshold: Stability threshold used
        flags: Optimization flags used
    
    Example:
        log_stability_failure("cfg_005", "layernorm", 1.2e-4, 3.5e-4, 1e-5, ["-O3", "-ffast-math"])
    """
    logger = get_logger()
    logger.warning(
        f"Stability failure: {kernel} config {config_id} exceeds threshold",
        extra={
            'warning_type': 'Stability Failure',
            'config_id': config_id,
            'kernel': kernel,
            'error_metric': f"L2={l2_error:.2e}, MaxDiff={max_diff:.2e}",
            'threshold': threshold,
            'flag_combination': flags
        }
    )


def main() -> None:
    """
    Command-line interface for testing the logger.
    
    Usage:
        python code/utils/logger.py --test
    
    This runs a series of test log entries to verify the logging infrastructure.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test logging infrastructure")
    parser.add_argument("--test", action="store_true", help="Run test log entries")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    
    args = parser.parse_args()
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    
    log_level = level_map.get(args.log_level.upper(), logging.INFO)
    
    # Setup logging
    logger = setup_logging(log_level=log_level, log_to_file=True)
    
    if args.test:
        logger.info("=== Logger Test Suite ===")
        
        # Test compiler version logging
        log_compiler_version("gcc", "11.4.0", ["-O2", "-march=native"])
        
        # Test flag combination logging
        log_flag_combination("cfg_001", ["-O3", "-ffast-math"], "matmul")
        log_flag_combination("cfg_002", ["-Os"], "softmax")
        
        # Test execution warnings
        log_execution_warning(
            "Memory Pressure",
            "768x768 allocation failed, downsampling to 512x512",
            config_id="cfg_003",
            kernel="matmul",
            details={"original_dim": "768x768", "downsampled_dim": "512x512"}
        )
        
        # Test NaN detection
        log_nan_detection(
            "cfg_004",
            "layernorm",
            "512x512",
            ["-O3", "-ffast-math", "-funroll-loops"],
            details={"nan_indices": [10, 42, 156]}
        )
        
        # Test stability failure
        log_stability_failure(
            "cfg_005",
            "matmul",
            l2_error=2.5e-4,
            max_diff=5.1e-4,
            threshold=1e-5,
            flags=["-O3", "-ffast-math"]
        )
        
        logger.info("=== Test Suite Complete ===")
        logger.info(f"Logs written to: {_log_file_path}")
    else:
        logger.info("Logging initialized. Use --test to run test suite.")


if __name__ == "__main__":
    main()
