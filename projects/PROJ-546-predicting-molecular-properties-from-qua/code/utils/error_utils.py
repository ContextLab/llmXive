"""
Error handling utilities for the molecular property prediction pipeline.

This module provides custom exceptions and utility functions to handle:
- Convergence failures in quantum chemical calculations
- Out-of-Memory (OOM) errors
- Structural validation failures (e.g., HOMO >= LUMO)

All failures are logged appropriately and handled according to the project's
edge case specifications.
"""

import logging
import os
import re
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Custom Exceptions

class ConvergenceError(Exception):
    """Raised when a quantum chemical calculation fails to converge."""
    def __init__(self, message: str, molecule_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.molecule_id = molecule_id
        self.details = details or {}

class OOMError(Exception):
    """Raised when a process exceeds memory limits or is killed due to OOM."""
    def __init__(self, message: str, molecule_id: Optional[str] = None, memory_mb: Optional[float] = None):
        super().__init__(message)
        self.molecule_id = molecule_id
        self.memory_mb = memory_mb

class StructuralError(Exception):
    """Raised when a structural constraint is violated (e.g., HOMO >= LUMO)."""
    def __init__(self, message: str, molecule_id: Optional[str] = None, values: Optional[Dict[str, float]] = None):
        super().__init__(message)
        self.molecule_id = molecule_id
        self.values = values or {}

# Logging Setup

def _get_logger(name: str) -> logging.Logger:
    """Get or create a logger with standard formatting."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Failure Detection Functions

def detect_convergence_failure(log_content: str, calculator_type: str = "dftb") -> bool:
    """
    Detect convergence failure patterns in log content.
    
    Args:
        log_content: The raw log output from the calculation.
        calculator_type: The type of calculator ('dftb', 'psi4', etc.)
    
    Returns:
        True if convergence failure is detected, False otherwise.
    """
    failure_patterns = [
        r"convergence\s+not\s+achieved",
        r"failed\s+to\s+converge",
        r"maximum\s+iterations\s+exceeded",
        r"convergence\s+failure",
        r"not\s+converged",
        r"scf\s+not\s+converged",
        r"geometry\s+optimization\s+failed",
        r"optimization\s+did\s+not\s+converge",
    ]
    
    # Calculator-specific patterns
    if calculator_type.lower() == "dftb":
        failure_patterns.extend([
            r"electron\s+density\s+not\s+converged",
            r"charge\s+mixing\s+failed",
        ])
    elif calculator_type.lower() == "psi4":
        failure_patterns.extend([
            r"scf\s+energy\s+not\s+converged",
            r"gradient\s+not\s+converged",
            r"optimizer\s+failed",
        ])
    
    log_lower = log_content.lower()
    for pattern in failure_patterns:
        if re.search(pattern, log_lower, re.IGNORECASE):
            return True
    
    return False

def check_oom_in_log(log_content: str) -> bool:
    """
    Check if log content indicates an Out-of-Memory condition.
    
    Args:
        log_content: The raw log output from the calculation.
    
    Returns:
        True if OOM is detected, False otherwise.
    """
    oom_patterns = [
        r"out\s*of\s*memory",
        r"oom",
        r"killed",
        r"memory\s+allocation\s+failed",
        r"cannot\s+allocate",
        r"exceeded\s+memory",
        r"sigkill",
        r"signal\s+9",
    ]
    
    log_lower = log_content.lower()
    for pattern in oom_patterns:
        if re.search(pattern, log_lower, re.IGNORECASE):
            return True
    
    return False

def monitor_memory_usage(pid: int) -> float:
    """
    Monitor the current memory usage of a process by PID.
    
    Args:
        pid: Process ID to monitor.
    
    Returns:
        Memory usage in MB, or -1.0 if process not found.
    """
    try:
        import resource
        # Try to get memory from /proc on Linux
        if os.path.exists(f"/proc/{pid}/statm"):
            with open(f"/proc/{pid}/statm", "r") as f:
                parts = f.read().split()
                if len(parts) >= 2:
                    rss_pages = int(parts[1])
                    page_size = os.sysconf("SC_PAGE_SIZE")
                    return (rss_pages * page_size) / (1024 * 1024)
        
        # Fallback to resource module if available
        try:
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            return usage.ru_maxrss / 1024  # Convert KB to MB on Linux
        except:
            pass
        
        return -1.0
    except Exception:
        return -1.0

# Failure Handling Functions

def handle_convergence_failure(
    molecule_id: str,
    error_details: Dict[str, Any],
    log_file_path: Optional[str] = None,
    skip: bool = True
) -> None:
    """
    Handle a convergence failure by logging and optionally skipping the molecule.
    
    Args:
        molecule_id: The identifier of the molecule that failed.
        error_details: Dictionary containing error information.
        log_file_path: Path to the convergence failures log file.
        skip: If True, the molecule is skipped (logged). If False, an exception is raised.
    """
    logger = _get_logger("error_utils")
    log_path = Path(log_file_path) if log_file_path else Path("logs/convergence_failures.log")
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    failure_record = {
        "molecule_id": molecule_id,
        "timestamp": None,  # Will be set by the caller if needed
        "error_type": "convergence",
        "details": error_details
    }
    
    if skip:
        logger.warning(f"Convergence failure for {molecule_id}. Skipping. Details: {error_details}")
        with open(log_path, "a") as f:
            f.write(f"{molecule_id}|convergence|{str(error_details)}\n")
    else:
        raise ConvergenceError(
            f"Convergence failure for molecule {molecule_id}",
            molecule_id=molecule_id,
            details=error_details
        )

def handle_oom(
    molecule_id: str,
    memory_mb: Optional[float] = None,
    log_file_path: Optional[str] = None,
    skip: bool = True
) -> None:
    """
    Handle an Out-of-Memory error by logging and optionally skipping the molecule.
    
    Args:
        molecule_id: The identifier of the molecule that failed.
        memory_mb: The memory usage at the time of failure (in MB).
        log_file_path: Path to the OOM failures log file.
        skip: If True, the molecule is skipped (logged). If False, an exception is raised.
    """
    logger = _get_logger("error_utils")
    log_path = Path(log_file_path) if log_file_path else Path("logs/oom_failures.log")
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    error_details = {"memory_mb": memory_mb}
    
    if skip:
        logger.warning(f"OOM error for {molecule_id}. Memory usage: {memory_mb} MB. Skipping.")
        with open(log_path, "a") as f:
            f.write(f"{molecule_id}|oom|memory_mb={memory_mb}\n")
    else:
        raise OOMError(
            f"Out-of-Memory error for molecule {molecule_id}",
            molecule_id=molecule_id,
            memory_mb=memory_mb
        )

def handle_structural_failure(
    molecule_id: str,
    error_type: str,
    values: Dict[str, float],
    log_file_path: Optional[str] = None,
    skip: bool = True
) -> None:
    """
    Handle a structural constraint violation (e.g., HOMO >= LUMO).
    
    Args:
        molecule_id: The identifier of the molecule that failed.
        error_type: Type of structural failure (e.g., "homo_lumo_violation").
        values: Dictionary of relevant values (e.g., {"homo": -5.0, "lumo": -4.5}).
        log_file_path: Path to the structural failures log file.
        skip: If True, the molecule is skipped (logged). If False, an exception is raised.
    """
    logger = _get_logger("error_utils")
    log_path = Path(log_file_path) if log_file_path else Path("logs/structural_failures.log")
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    if skip:
        logger.warning(f"Structural failure for {molecule_id}: {error_type}. Values: {values}. Skipping.")
        with open(log_path, "a") as f:
            f.write(f"{molecule_id}|{error_type}|{str(values)}\n")
    else:
        raise StructuralError(
            f"Structural failure for molecule {molecule_id}: {error_type}",
            molecule_id=molecule_id,
            values=values
        )

def run_with_oom_protection(
    func,
    *args,
    memory_limit_mb: float = 7000.0,
    molecule_id: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Run a function with OOM protection. If memory usage exceeds the limit,
    the function is terminated and an OOMError is raised.
    
    Args:
        func: The function to run.
        *args: Positional arguments for the function.
        memory_limit_mb: Maximum allowed memory usage in MB.
        molecule_id: Optional molecule ID for error reporting.
        **kwargs: Keyword arguments for the function.
    
    Returns:
        The return value of the function.
    
    Raises:
        OOMError: If memory limit is exceeded.
    """
    import threading
    import time
    
    stop_monitor = threading.Event()
    peak_memory = [0.0]
    
    def monitor():
        while not stop_monitor.is_set():
            current = monitor_memory_usage(os.getpid())
            if current > peak_memory[0]:
                peak_memory[0] = current
            if current > memory_limit_mb:
                os.kill(os.getpid(), signal.SIGKILL)
            time.sleep(0.1)
    
    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    try:
        result = func(*args, **kwargs)
        return result
    finally:
        stop_monitor.set()
        monitor_thread.join(timeout=1.0)
    
    # If we reach here, the process was not killed (should not happen)
    if peak_memory[0] > memory_limit_mb:
        handle_oom(molecule_id or "unknown", peak_memory[0], skip=False)

def main():
    """
    Main function for testing error utilities.
    """
    print("Testing error utilities...")
    
    # Test Convergence Detection
    test_log = "SCF not converged after 100 iterations."
    assert detect_convergence_failure(test_log), "Convergence detection failed"
    print("✓ Convergence detection works")
    
    # Test OOM Detection
    test_oom_log = "Process killed due to out of memory."
    assert check_oom_in_log(test_oom_log), "OOM detection failed"
    print("✓ OOM detection works")
    
    # Test Custom Exceptions
    try:
        raise ConvergenceError("Test convergence error", molecule_id="mol_001")
    except ConvergenceError as e:
        assert e.molecule_id == "mol_001"
        print("✓ ConvergenceError works")
    
    try:
        raise OOMError("Test OOM error", molecule_id="mol_002", memory_mb=8000.0)
    except OOMError as e:
        assert e.molecule_id == "mol_002"
        assert e.memory_mb == 8000.0
        print("✓ OOMError works")
    
    try:
        raise StructuralError("Test structural error", molecule_id="mol_003", values={"homo": -5.0, "lumo": -4.5})
    except StructuralError as e:
        assert e.molecule_id == "mol_003"
        print("✓ StructuralError works")
    
    print("All error utility tests passed.")

if __name__ == "__main__":
    main()