"""
Error handling utilities for molecular property prediction pipeline.

This module provides custom exceptions and logging utilities to handle
convergence failures and Out-Of-Memory (OOM) signals during quantum
chemical calculations.
"""

import logging
import os
import re
import signal
import sys
from pathlib import Path
from typing import Optional


class ConvergenceError(Exception):
    """Exception raised when a geometry optimization or SCF calculation fails to converge."""
    
    def __init__(self, message: str, molecule_id: Optional[str] = None, details: Optional[str] = None):
        self.molecule_id = molecule_id
        self.details = details
        full_message = message
        if molecule_id:
            full_message = f"[{molecule_id}] {message}"
        if details:
            full_message += f" | Details: {details}"
        super().__init__(full_message)


class OOMError(Exception):
    """Exception raised when a calculation is terminated due to memory exhaustion."""
    
    def __init__(self, message: str, molecule_id: Optional[str] = None, memory_limit_mb: Optional[float] = None):
        self.molecule_id = molecule_id
        self.memory_limit_mb = memory_limit_mb
        full_message = message
        if molecule_id:
            full_message = f"[{molecule_id}] {message}"
        if memory_limit_mb:
            full_message += f" (Limit: {memory_limit_mb} MB)"
        super().__init__(full_message)


def setup_logger(log_file_path: str, name: str = "error_handler") -> logging.Logger:
    """
    Set up a logger that writes to a specific file.
    
    Args:
        log_file_path: Path to the log file.
        name: Logger name.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        # Ensure directory exists
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger


def log_convergence_failure(
    logger: logging.Logger,
    molecule_id: str,
    error_message: str,
    details: Optional[str] = None
) -> None:
    """
    Log a convergence failure to the specified logger.
    
    Args:
        logger: Logger instance to write to.
        molecule_id: Unique identifier for the molecule.
        error_message: Description of the convergence failure.
        details: Optional additional details (e.g., DFTB+ log snippet).
    """
    msg = f"CONVERGENCE_FAILURE | molecule_id={molecule_id} | error={error_message}"
    if details:
        msg += f" | details={details}"
    logger.error(msg)

def log_oom_failure(
    logger: logging.Logger,
    molecule_id: str,
    error_message: str,
    memory_limit_mb: Optional[float] = None
) -> None:
    """
    Log an Out-Of-Memory failure to the specified logger.
    
    Args:
        logger: Logger instance to write to.
        molecule_id: Unique identifier for the molecule.
        error_message: Description of the OOM event.
        memory_limit_mb: Optional memory limit that was exceeded.
    """
    msg = f"OOM_FAILURE | molecule_id={molecule_id} | error={error_message}"
    if memory_limit_mb:
        msg += f" | limit_mb={memory_limit_mb}"
    logger.error(msg)

def detect_convergence_failure(log_content: str) -> bool:
    """
    Detect convergence failure patterns in log content.
    
    Args:
        log_content: String content of the calculation log.
        
    Returns:
        True if convergence failure is detected, False otherwise.
    """
    patterns = [
        r"convergence.*not.*achieved",
        r"failed.*converge",
        r"maximum.*iterations.*exceeded",
        r"scf.*not.*converged",
        r"geometry.*optimization.*failed",
        r"error.*convergence"
    ]
    
    log_lower = log_content.lower()
    for pattern in patterns:
        if re.search(pattern, log_lower):
            return True
    return False

def check_oom_in_log(log_content: str) -> bool:
    """
    Check if the log content indicates an OOM termination.
    
    Args:
        log_content: String content of the log.
        
    Returns:
        True if OOM is detected, False otherwise.
    """
    patterns = [
        r"out.*of.*memory",
        r"oom",
        r"killed",
        r"memory.*exceeded",
        r"allocation.*failed"
    ]
    
    log_lower = log_content.lower()
    for pattern in patterns:
        if re.search(pattern, log_lower):
            return True
    return False

def handle_convergence_failure(
    molecule_id: str,
    error_message: str,
    log_path: str,
    details: Optional[str] = None
) -> None:
    """
    Handle a convergence failure by logging it and skipping the molecule.
    
    Args:
        molecule_id: Unique identifier for the molecule.
        error_message: Description of the failure.
        log_path: Path to the convergence failures log file.
        details: Optional additional details.
    """
    logger = setup_logger(log_path)
    log_convergence_failure(logger, molecule_id, error_message, details)
    # The caller should catch the exception and skip processing this molecule

def handle_oom(
    molecule_id: str,
    error_message: str,
    log_path: str,
    memory_limit_mb: Optional[float] = None
) -> None:
    """
    Handle an OOM failure by logging it and skipping the molecule.
    
    Args:
        molecule_id: Unique identifier for the molecule.
        error_message: Description of the failure.
        log_path: Path to the OOM failures log file.
        memory_limit_mb: Optional memory limit that was exceeded.
    """
    logger = setup_logger(log_path)
    log_oom_failure(logger, molecule_id, error_message, memory_limit_mb)
    # The caller should catch the exception and skip processing this molecule

def monitor_memory_usage(threshold_mb: float) -> bool:
    """
    Monitor the current process memory usage.
    
    Args:
        threshold_mb: Memory threshold in MB.
        
    Returns:
        True if current usage exceeds threshold, False otherwise.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        current_mb = usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux
        return current_mb > threshold_mb
    except Exception:
        # If we can't check, assume safe
        return False

def run_with_oom_protection(func, *args, threshold_mb: float = 6000, **kwargs):
    """
    Wrapper to run a function with OOM protection.
    
    Args:
        func: Function to run.
        *args: Arguments to pass to the function.
        threshold_mb: Memory threshold in MB.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        Result of the function.
        
    Raises:
        OOMError: If memory threshold is exceeded during execution.
    """
    import resource
    
    # Set a soft limit to trigger SIGXCPU before hard crash
    try:
        current_soft, current_hard = resource.getrlimit(resource.RLIMIT_AS)
        # Limit to 1.5x threshold roughly (in bytes)
        limit_bytes = int(threshold_mb * 1024 * 1024 * 1.5)
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, current_hard))
    except ValueError:
        pass # Platform might not support this
    
    def handler(signum, frame):
        raise OOMError("Process terminated due to memory limit", memory_limit_mb=threshold_mb)
    
    old_handler = signal.signal(signal.SIGXCPU, handler)
    try:
        return func(*args, **kwargs)
    finally:
        signal.signal(signal.SIGXCPU, old_handler)
        # Reset limits if we want (optional)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (current_soft, current_hard))
        except ValueError:
            pass

def check_process_memory() -> float:
    """
    Get current peak memory usage of the process in MB.
    
    Returns:
        Memory usage in MB.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0
    except Exception:
        return 0.0

def main():
    """
    Main entry point for testing error handlers.
    This is a simple test to verify the logging setup works.
    """
    import tempfile
    import os
    
    # Create a temporary log file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as tmp:
        log_path = tmp.name
    
    try:
        logger = setup_logger(log_path, "test_error_handler")
        
        # Test convergence failure
        handle_convergence_failure(
            molecule_id="TEST_001",
            error_message="SCF did not converge after 100 iterations",
            log_path=log_path,
            details="Last energy: -123.456"
        )
        
        # Test OOM failure
        handle_oom(
            molecule_id="TEST_002",
            error_message="Memory limit exceeded",
            log_path=log_path,
            memory_limit_mb=1024.0
        )
        
        # Verify log content
        with open(log_path, 'r') as f:
            content = f.read()
            print("Log content:")
            print(content)
            
            assert "CONVERGENCE_FAILURE" in content
            assert "TEST_001" in content
            assert "OOM_FAILURE" in content
            assert "TEST_002" in content
            
        print("Test passed: Error handlers logging correctly.")
        
    finally:
        if os.path.exists(log_path):
            os.remove(log_path)

if __name__ == "__main__":
    main()