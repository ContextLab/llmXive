"""
Error handling utilities for molecular property prediction pipeline.

This module provides specialized exception classes and handlers for:
- Convergence failures in quantum chemistry calculations
- Out-of-memory (OOM) conditions during computation
- Structured logging of failures to dedicated log files
"""

import logging
import os
import re
import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

CONVERGENCE_LOG = LOGS_DIR / "convergence_failures.log"
OOM_LOG = LOGS_DIR / "oom_failures.log"

# Custom exception classes
class ConvergenceError(Exception):
    """Raised when a quantum chemistry calculation fails to converge."""
    def __init__(self, molecule_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.molecule_id = molecule_id
        self.details = details or {}

class OOMError(Exception):
    """Raised when a calculation exceeds available memory."""
    def __init__(self, molecule_id: str, message: str, memory_usage_mb: Optional[float] = None):
        super().__init__(message)
        self.molecule_id = molecule_id
        self.memory_usage_mb = memory_usage_mb

def setup_logger(log_path: Path) -> logging.Logger:
    """
    Set up a file logger that writes to the specified path.
    
    Args:
        log_path: Path to the log file.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(log_path.stem)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if logger already exists
    if not logger.handlers:
        fh = logging.FileHandler(log_path, mode='a')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def log_convergence_failure(molecule_id: str, message: str, details: Optional[Dict[str, Any]] = None):
    """
    Log a convergence failure to the dedicated log file.
    
    Args:
        molecule_id: Identifier of the molecule that failed.
        message: Description of the failure.
        details: Optional dictionary of additional context (e.g., iteration count, energy values).
    """
    logger = setup_logger(CONVERGENCE_LOG)
    log_entry = f"MOLECULE_ID={molecule_id} | STATUS=failed | REASON={message}"
    if details:
        details_str = ", ".join(f"{k}={v}" for k, v in details.items())
        log_entry += f" | DETAILS={details_str}"
    logger.info(log_entry)

def log_oom_failure(molecule_id: str, message: str, memory_usage_mb: Optional[float] = None):
    """
    Log an out-of-memory failure to the dedicated log file.
    
    Args:
        molecule_id: Identifier of the molecule that failed.
        message: Description of the failure.
        memory_usage_mb: Optional memory usage at failure time.
    """
    logger = setup_logger(OOM_LOG)
    log_entry = f"MOLECULE_ID={molecule_id} | STATUS=failed | REASON={message}"
    if memory_usage_mb is not None:
        log_entry += f" | MEMORY_MB={memory_usage_mb:.2f}"
    logger.info(log_entry)

def detect_convergence_failure(output_text: str) -> bool:
    """
    Detect convergence failure from calculation output text.
    
    Args:
        output_text: The stdout/stderr output from the quantum chemistry run.
        
    Returns:
        True if convergence failure is detected, False otherwise.
    """
    # Common patterns indicating convergence failure in DFTB+/Psi4 outputs
    convergence_patterns = [
        r"convergence.*not.*reached",
        r"failed.*to.*converge",
        r"maximum.*iterations.*exceeded",
        r"scf.*not.*converged",
        r"cycle.*did.*not.*converge",
        r"electronic.*convergence.*failed",
    ]
    
    output_lower = output_text.lower()
    for pattern in convergence_patterns:
        if re.search(pattern, output_lower):
            return True
    return False

def check_oom_in_log(log_text: str) -> bool:
    """
    Detect OOM conditions from log text.
    
    Args:
        log_text: The log output text.
        
    Returns:
        True if OOM condition is detected, False otherwise.
    """
    oom_patterns = [
        r"out.*of.*memory",
        r"oom",
        r"memory.*allocation.*failed",
        r"cannot.*allocate",
        r"exceeded.*memory.*limit",
        r"killed.*process",
    ]
    
    log_lower = log_text.lower()
    for pattern in oom_patterns:
        if re.search(pattern, log_lower):
            return True
    return False

def handle_convergence_failure(molecule_id: str, output_text: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Handle a convergence failure by logging it and raising a ConvergenceError.
    
    Args:
        molecule_id: Identifier of the molecule.
        output_text: The output text from the calculation.
        details: Optional additional context.
        
    Raises:
        ConvergenceError: Always raised to signal the caller to skip this molecule.
    """
    # Extract relevant error snippet if available
    error_snippet = "Convergence not reached"
    if output_text:
        lines = output_text.split('\n')
        for line in lines[-10:]:  # Check last 10 lines for specific error
            if re.search(r"convergence.*not.*reached|failed.*to.*converge", line.lower()):
                error_snippet = line.strip()
                break
    
    log_convergence_failure(molecule_id, error_snippet, details)
    raise ConvergenceError(molecule_id, error_snippet, details)

def handle_oom(molecule_id: str, memory_usage_mb: Optional[float] = None) -> None:
    """
    Handle an out-of-memory condition by logging it and raising an OOMError.
    
    Args:
        molecule_id: Identifier of the molecule.
        memory_usage_mb: Memory usage at failure time.
        
    Raises:
        OOMError: Always raised to signal the caller to skip this molecule.
    """
    log_oom_failure(molecule_id, "Memory limit exceeded", memory_usage_mb)
    raise OOMError(molecule_id, "Memory limit exceeded", memory_usage_mb)

def monitor_memory_usage(threshold_mb: float = 6000.0) -> None:
    """
    Monitor current process memory usage and raise OOMError if threshold exceeded.
    
    Args:
        threshold_mb: Memory threshold in MB (default 6000 MB).
        
    Raises:
        OOMError: If current memory usage exceeds threshold.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on some systems; normalize to MB
        max_rss_kb = usage.ru_maxrss
        if sys.platform != 'darwin' and sys.platform != 'win32':
            # Linux reports in KB
            max_rss_mb = max_rss_kb / 1024.0
        else:
            # macOS reports in bytes
            max_rss_mb = max_rss_kb / (1024.0 * 1024.0)
        
        if max_rss_mb > threshold_mb:
            handle_oom("current_process", max_rss_mb)
    except Exception:
        # If we can't check, just continue (fail-safe)
        pass

def run_with_oom_protection(func, molecule_id: str, *args, **kwargs):
    """
    Run a function with OOM protection.
    
    Args:
        func: The function to run.
        molecule_id: Identifier of the molecule being processed.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The result of the function if successful.
        
    Raises:
        OOMError: If OOM condition is detected.
        Any other exception raised by func.
    """
    try:
        return func(*args, **kwargs)
    except MemoryError:
        handle_oom(molecule_id)
    except OOMError:
        raise
    except Exception as e:
        # Check if it's an OOM signal from subprocess
        if isinstance(e, subprocess.SubprocessError):
            if hasattr(e, 'stderr') and e.stderr:
                if check_oom_in_log(str(e.stderr)):
                    handle_oom(molecule_id)
        raise

# For use in subprocess monitoring
def check_process_memory(pid: int, threshold_mb: float = 6000.0) -> bool:
    """
    Check if a specific process exceeds memory threshold.
    
    Args:
        pid: Process ID to check.
        threshold_mb: Memory threshold in MB.
        
    Returns:
        True if process exceeds threshold, False otherwise.
    """
    try:
        import psutil
        process = psutil.Process(pid)
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / (1024.0 * 1024.0)
        return mem_mb > threshold_mb
    except ImportError:
        # psutil not available, fallback to resource if same process
        if pid == os.getpid():
            try:
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                max_rss_kb = usage.ru_maxrss
                if sys.platform != 'darwin' and sys.platform != 'win32':
                    max_rss_mb = max_rss_kb / 1024.0
                else:
                    max_rss_mb = max_rss_kb / (1024.0 * 1024.0)
                return max_rss_mb > threshold_mb
            except Exception:
                return False
        return False
    except Exception:
        return False

def main():
    """
    Demonstrate error handling functionality.
    """
    # Test logging
    log_convergence_failure("TEST-MOL-001", "SCF did not converge after 200 iterations", {"iterations": 200, "energy": -12.345})
    log_oom_failure("TEST-MOL-002", "Out of memory", 7500.5)
    
    print("Error handlers initialized and logs written.")
    print(f"Convergence log: {CONVERGENCE_LOG}")
    print(f"OOM log: {OOM_LOG}")

if __name__ == "__main__":
    main()