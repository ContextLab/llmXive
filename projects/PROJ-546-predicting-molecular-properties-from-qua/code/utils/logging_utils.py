"""
Logging utilities for DFTB+ and Psi4 quantum chemistry workflows.

Provides structured logging for invocation details, timing metrics, and resource usage
to support reproducibility and performance analysis.
"""
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
import resource

# Configure a dedicated logger for quantum chemistry workflows
LOGGER_NAME = "quantum_workflow"
logger = logging.getLogger(LOGGER_NAME)

# Default log format with timestamp, level, and message
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logger(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the quantum workflow logger with optional file output.
    
    Args:
        log_file: Path to log file. If None, only console output is used.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    
    Returns:
        Configured logger instance.
    """
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
        logger.addHandler(file_handler)
    
    return logger

def log_dftb_invocation(smiles: str, work_dir: str, input_file: str, log_file: str) -> None:
    """
    Log the start of a DFTB+ invocation with key parameters.
    
    Args:
        smiles: SMILES string of the molecule.
        work_dir: Working directory for the calculation.
        input_file: Path to the DFTB+ input file.
        log_file: Path to the DFTB+ output log file.
    """
    logger.info(f"DFTB+ invocation started for SMILES: {smiles}")
    logger.debug(f"Working directory: {work_dir}")
    logger.debug(f"Input file: {input_file}")
    logger.debug(f"Output log: {log_file}")

def log_psi4_invocation(smiles: str, work_dir: str, input_file: str, log_file: str) -> None:
    """
    Log the start of a Psi4 invocation with key parameters.
    
    Args:
        smiles: SMILES string of the molecule.
        work_dir: Working directory for the calculation.
        input_file: Path to the Psi4 input file.
        log_file: Path to the Psi4 output log file.
    """
    logger.info(f"Psi4 invocation started for SMILES: {smiles}")
    logger.debug(f"Working directory: {work_dir}")
    logger.debug(f"Input file: {input_file}")
    logger.debug(f"Output log: {log_file}")

@contextmanager
def timed_section(section_name: str, logger_instance: Optional[logging.Logger] = None):
    """
    Context manager to log the execution time of a code section.
    
    Args:
        section_name: Name of the section being timed.
        logger_instance: Logger to use. Defaults to the module logger.
    
    Yields:
        None
    """
    log = logger_instance or logger
    start_time = time.time()
    log.debug(f"Starting {section_name}")
    
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        log.info(f"{section_name} completed in {elapsed:.2f} seconds")

def get_resource_usage() -> Dict[str, Any]:
    """
    Get current process resource usage.
    
    Returns:
        Dictionary containing memory usage (RSS in bytes) and other metrics.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "max_rss_bytes": usage.ru_maxrss * 1024,  # Convert KB to bytes on Linux
        "user_time_seconds": usage.ru_utime,
        "system_time_seconds": usage.ru_stime,
    }

def log_resource_snapshot(stage: str, logger_instance: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Log a snapshot of resource usage at a specific stage.
    
    Args:
        stage: Name of the current stage (e.g., "before_optimization", "after_optimization").
        logger_instance: Logger to use. Defaults to the module logger.
    
    Returns:
        Dictionary with resource metrics.
    """
    log = logger_instance or logger
    usage = get_resource_usage()
    
    log.info(f"Resource usage at {stage}:")
    log.info(f"  Max RSS: {usage['max_rss_bytes'] / (1024*1024):.2f} MB")
    log.info(f"  User time: {usage['user_time_seconds']:.2f} s")
    log.info(f"  System time: {usage['system_time_seconds']:.2f} s")
    
    return usage

def log_calculation_summary(smiles: str, method: str, success: bool, duration: float, 
                             resource_usage: Optional[Dict[str, Any]] = None, 
                             log_file: Optional[str] = None) -> None:
    """
    Log a summary of a completed calculation.
    
    Args:
        smiles: SMILES string of the molecule.
        method: Computational method used (e.g., "DFTB+", "Psi4").
        success: Whether the calculation completed successfully.
        duration: Total duration in seconds.
        resource_usage: Optional dictionary of resource metrics.
        log_file: Optional path to append summary to a file.
    """
    status = "SUCCESS" if success else "FAILURE"
    log_msg = f"{method} calculation for {smiles}: {status} (duration: {duration:.2f}s)"
    
    logger.info(log_msg)
    
    if resource_usage:
        logger.info(f"  Peak memory: {resource_usage['max_rss_bytes'] / (1024*1024):.2f} MB")
        logger.info(f"  Total time: {resource_usage['user_time_seconds'] + resource_usage['system_time_seconds']:.2f} s")
    
    # Append to file if specified
    if log_file:
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} | {log_msg}\n")
            if resource_usage:
                f.write(f"  Peak memory: {resource_usage['max_rss_bytes'] / (1024*1024):.2f} MB\n")
                f.write(f"  Total time: {resource_usage['user_time_seconds'] + resource_usage['system_time_seconds']:.2f} s\n")

def main():
    """
    Demonstration of logging utilities.
    """
    # Setup logger with file output
    log_file = os.path.join(os.path.dirname(__file__), "..", "logs", "workflow_demo.log")
    setup_logger(log_file=log_file, level=logging.DEBUG)
    
    logger.info("Demonstrating logging utilities")
    
    # Example: timed section
    with timed_section("example_operation"):
        time.sleep(0.5)
    
    # Example: resource snapshot
    log_resource_snapshot("demo_stage")
    
    # Example: calculation summary
    log_calculation_summary(
        smiles="CCO",
        method="DFTB+",
        success=True,
        duration=12.5,
        resource_usage={"max_rss_bytes": 500 * 1024 * 1024, "user_time_seconds": 10.0, "system_time_seconds": 2.5},
        log_file=log_file
    )
    
    print(f"Demo logs written to: {os.path.abspath(log_file)}")

if __name__ == "__main__":
    main()