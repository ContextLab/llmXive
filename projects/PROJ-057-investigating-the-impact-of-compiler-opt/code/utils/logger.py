"""
Logging infrastructure for the compiler optimization impact study.

This module provides a centralized logging setup to record:
- Compiler versions detected during the experiment
- Flag combinations used for compilation
- Runtime warnings, specifically NaN detection events
- General execution flow and errors

Usage:
    from utils.logger import get_logger, setup_logging
    logger = get_logger()
    logger.info("Starting benchmark...")
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Ensure the log directory exists
LOG_DIR = Path(__file__).parent.parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Format string including timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance cache to prevent re-initialization issues
_logger_instance: Optional[logging.Logger] = None

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    Configure the root logger for the project.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to a log file. If None, uses default data/logs/project.log
        enable_console: Whether to log to stdout/stderr
    """
    global _logger_instance

    # Default log file path
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = str(LOG_DIR / f"experiment_{timestamp}.log")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-runs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # File Handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if file write fails (e.g., permission issues)
        print(f"Warning: Could not create log file {log_file}: {e}", file=sys.stderr)

    # Console Handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Set specific level for third-party libraries if needed
    logging.getLogger("numpy").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

def get_logger(name: str = "compiler_opt") -> logging.Logger:
    """
    Retrieve a named logger instance.

    Args:
        name: Name of the logger (e.g., 'compiler_opt.executor')

    Returns:
        Configured logging.Logger instance
    """
    return logging.getLogger(name)

def log_compiler_version(
    logger: logging.Logger,
    compiler: str,
    version_info: str,
    flags: List[str]
) -> None:
    """
    Log the compiler version and the flags used.

    Args:
        logger: The logger instance to use
        compiler: Name of the compiler (e.g., 'g++', 'clang++')
        version_info: Output from compiler version command
        flags: List of optimization flags used
    """
    logger.info(f"Compiler detected: {compiler}")
    logger.info(f"Version info: {version_info.strip()}")
    logger.info(f"Optimization flags: {' '.join(flags)}")

def log_nan_detection(
    logger: logging.Logger,
    config_id: str,
    kernel_type: str,
    tensor_shape: str,
    details: Optional[str] = None
) -> None:
    """
    Log a runtime warning regarding NaN detection in output tensors.

    This is a critical stability check that should be flagged prominently.

    Args:
        logger: The logger instance to use
        config_id: Unique identifier for the configuration
        kernel_type: Type of kernel (e.g., 'matmul', 'softmax')
        tensor_shape: Shape of the tensor where NaN was found
        details: Optional additional details about the detection
    """
    message = f"CRITICAL: NaN detected in output for config={config_id}, kernel={kernel_type}, shape={tensor_shape}"
    if details:
        message += f" | Details: {details}"

    logger.warning(message)

    # Also log to a specific warning file for easy auditing
    warning_file = LOG_DIR / "nan_warnings.jsonl"
    try:
        with open(warning_file, "a", encoding="utf-8") as f:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "config_id": config_id,
                "kernel_type": kernel_type,
                "tensor_shape": tensor_shape,
                "details": details,
                "type": "nan_detection"
            }
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write NaN warning to audit file: {e}")

def log_execution_warning(
    logger: logging.Logger,
    config_id: str,
    warning_type: str,
    message: str
) -> None:
    """
    Log a general runtime warning.

    Args:
        logger: The logger instance to use
        config_id: Unique identifier for the configuration
        warning_type: Category of warning (e.g., 'memory_pressure', 'timeout')
        message: The warning message
    """
    full_message = f"[{warning_type}] Config {config_id}: {message}"
    logger.warning(full_message)

def log_stability_failure(
    logger: logging.Logger,
    config_id: str,
    kernel_type: str,
    error_metric: str,
    error_value: float,
    threshold: float
) -> None:
    """
    Log a stability failure where error exceeds the threshold.

    Args:
        logger: The logger instance to use
        config_id: Unique identifier for the configuration
        kernel_type: Type of kernel
        error_metric: Name of the metric (e.g., 'l2_relative_error')
        error_value: The calculated error value
        threshold: The threshold that was exceeded
    """
    message = (
        f"STABILITY FAILURE: Config {config_id}, Kernel {kernel_type} - "
        f"{error_metric}={error_value:.2e} exceeds threshold {threshold:.2e}"
    )
    logger.warning(message)

def main():
    """
    Main entry point for testing the logging infrastructure.
    """
    setup_logging(level=logging.DEBUG)
    logger = get_logger("compiler_opt.test")

    logger.info("Logging infrastructure initialized successfully.")
    
    # Simulate logging compiler info
    log_compiler_version(
        logger, 
        "g++", 
        "g++ (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0", 
        ["-O2", "-march=native"]
    )

    # Simulate a NaN detection event
    log_nan_detection(
        logger,
        config_id="test_config_001",
        kernel_type="matmul",
        tensor_shape="(768, 768)",
        details="First NaN found at index (12, 45)"
    )

    # Simulate a stability failure
    log_stability_failure(
        logger,
        config_id="test_config_002",
        kernel_type="softmax",
        error_metric="max_abs_diff",
        error_value=1.5e-4,
        threshold=1e-5
    )

    logger.info("Test logging sequence completed.")

if __name__ == "__main__":
    main()