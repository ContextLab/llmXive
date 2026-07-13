"""
Error handling utilities for quantum chemical calculations.

This module provides utilities to:
1. Detect convergence failures in DFTB+/Psi4 output logs.
2. Detect Out-Of-Memory (OOM) conditions.
3. Monitor subprocess memory usage in real-time.
4. Handle errors by skipping molecules or logging detailed warnings.
5. Kill subprocesses that exceed memory limits.
"""

import logging
import os
import re
import signal
import subprocess
import sys
import time
from typing import Optional, List, Tuple, Callable, Any

# Configure logger for this module
logger = logging.getLogger(__name__)

# Custom Exceptions
class ConvergenceError(Exception):
    """Raised when a quantum calculation fails to converge."""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.details = details

class OOMError(Exception):
    """Raised when a calculation exceeds memory limits."""
    def __init__(self, message: str, pid: Optional[int] = None):
        super().__init__(message)
        self.pid = pid


# --- Convergence Detection ---

def detect_convergence_failure(log_content: str) -> bool:
    """
    Detects convergence failure in quantum chemistry log output.

    Checks for common failure patterns in DFTB+ and Psi4 outputs.

    Args:
        log_content: The full text content of the output log file.

    Returns:
        True if convergence failure is detected, False otherwise.
    """
    if not log_content:
        return False

    # Common patterns for convergence failure
    failure_patterns = [
        r"convergence.*failed",
        r"did not converge",
        r"maximum.*exceeded",
        r"SCF.*convergence.*failure",
        r"calculation.*terminated",
        r"error.*convergence",
        r"no.*convergence",
        r"failed to converge",
        r"convergence.*not reached",
        r"max.*iterations.*exceeded",
        # DFTB+ specific
        r"Error.*convergence",
        r"Warning.*convergence",
        # Psi4 specific
        r"ConvergenceFailure",
        r"SCF.*convergence.*failed",
    ]

    lower_content = log_content.lower()
    for pattern in failure_patterns:
        if re.search(pattern, lower_content, re.IGNORECASE):
            logger.debug(f"Convergence failure pattern detected: {pattern}")
            return True

    # Check for early termination without success markers
    success_markers = [
        "converged",
        "calculation terminated successfully",
        "energy:",
        "final energy",
    ]
    
    has_success = any(re.search(marker, lower_content) for marker in success_markers)
    has_error = any(re.search(p, lower_content, re.IGNORECASE) for p in failure_patterns)

    # If we see errors and no success, assume failure
    if has_error and not has_success:
        return True
        
    return False


def check_oom_in_log(log_content: str) -> bool:
    """
    Detects Out-Of-Memory (OOM) conditions in log output.

    Checks for common OOM error patterns.

    Args:
        log_content: The full text content of the output log file.

    Returns:
        True if OOM is detected, False otherwise.
    """
    if not log_content:
        return False

    oom_patterns = [
        r"out of memory",
        r"oom",
        r"memory allocation failed",
        r"cannot allocate memory",
        r"exceeded memory limit",
        r"segfault",
        r"segmentation fault",
        r"killed", # Often indicates OOM killer
    ]

    lower_content = log_content.lower()
    for pattern in oom_patterns:
        if re.search(pattern, lower_content, re.IGNORECASE):
            logger.debug(f"OOM pattern detected: {pattern}")
            return True

    return False


# --- Memory Monitoring ---

def monitor_memory_usage(pid: int) -> Optional[int]:
    """
    Monitors the RSS (Resident Set Size) of a process by PID.

    Args:
        pid: Process ID to monitor.

    Returns:
        Current RSS in bytes, or None if process not found.
    """
    try:
        if sys.platform == "linux" or sys.platform == "linux2":
            # Linux: read from /proc/<pid>/status
            status_path = f"/proc/{pid}/status"
            if os.path.exists(status_path):
                with open(status_path, 'r') as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            # Format: "VmRSS:    12345 kB"
                            parts = line.split()
                            if len(parts) >= 2:
                                rss_kb = int(parts[1])
                                return rss_kb * 1024 # Convert to bytes
        elif sys.platform == "darwin":
            # macOS: use ps command
            proc = subprocess.Popen(
                ["ps", "-o", "rss=", "-p", str(pid)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = proc.communicate()
            if proc.returncode == 0 and stdout:
                rss_kb = int(stdout.decode().strip())
                return rss_kb * 1024
        else:
            logger.warning("Memory monitoring not implemented for this OS.")
            return None

    except (ProcessLookupError, ValueError, FileNotFoundError, PermissionError):
        # Process likely terminated or we don't have permission
        return None

    return None


# --- Error Handling Logic ---

def handle_convergence_failure(
    molecule_id: str,
    log_path: str,
    skip: bool = True,
    log_level: int = logging.WARNING
) -> Tuple[bool, str]:
    """
    Handles a detected convergence failure.

    Args:
        molecule_id: Identifier for the molecule being processed.
        log_path: Path to the log file containing the failure.
        skip: If True, the molecule will be skipped (returns False).
              If False, an exception is raised.
        log_level: The logging level to use for the warning/error.

    Returns:
        A tuple (success, message).
        If skip=True: (False, "Skipped <id> due to convergence failure")
        If skip=False: (True, "") but raises ConvergenceError
    """
    message = f"Molecule {molecule_id} failed convergence."
    
    # Log the issue
    if log_level == logging.ERROR:
        logger.error(message)
    else:
        logger.log(log_level, message)

    if log_path and os.path.exists(log_path):
        logger.log(log_level, f"Log file: {log_path}")
        # Read last few lines for context
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
                tail = lines[-10:] if len(lines) > 10 else lines
                logger.log(log_level, "Last 10 lines of log:")
                for line in tail:
                    logger.log(log_level, f"  {line.strip()}")
        except Exception as e:
            logger.warning(f"Could not read log file for context: {e}")

    if skip:
        return False, f"Skipped {molecule_id} due to convergence failure."
    else:
        raise ConvergenceError(
            message,
            details=f"Check log file at {log_path}"
        )


def handle_oom(
    molecule_id: str,
    pid: Optional[int] = None,
    skip: bool = True,
    log_level: int = logging.ERROR
) -> Tuple[bool, str]:
    """
    Handles an Out-Of-Memory condition.

    Args:
        molecule_id: Identifier for the molecule.
        pid: Process ID of the failing subprocess.
        skip: If True, the molecule is skipped.
        log_level: Logging level.

    Returns:
        A tuple (success, message).
    """
    message = f"Molecule {molecule_id} triggered OOM protection."
    
    if log_level == logging.ERROR:
        logger.error(message)
    else:
        logger.log(log_level, message)

    if pid:
        logger.log(log_level, f"Process ID: {pid}")
        # Kill the process if it's still running
        try:
            os.kill(pid, signal.SIGKILL)
            logger.info(f"Killed process {pid} due to OOM.")
        except ProcessLookupError:
            logger.info(f"Process {pid} already terminated.")
        except PermissionError:
            logger.warning(f"Permission denied to kill process {pid}.")

    if skip:
        return False, f"Skipped {molecule_id} due to OOM. Consider reducing subset size."
    else:
        raise OOMError(message, pid=pid)


def run_with_oom_protection(
    cmd: List[str],
    molecule_id: str,
    memory_limit_gb: float = 6.5,
    check_interval: float = 1.0
) -> Tuple[Optional[subprocess.CompletedProcess], bool, str]:
    """
    Runs a subprocess with real-time memory monitoring.
    
    If the subprocess exceeds `memory_limit_gb`, it is killed and an OOM error
    is handled.

    Args:
        cmd: Command and arguments to run.
        molecule_id: Identifier for the molecule.
        memory_limit_gb: Memory limit in Gigabytes.
        check_interval: Seconds between memory checks.

    Returns:
        Tuple of (completed_process, success, message).
        - If success: (CompletedProcess, True, "Success")
        - If OOM: (None, False, "Skipped due to OOM")
        - If other error: (CompletedProcess, False, "Error message")
    """
    limit_bytes = int(memory_limit_gb * 1024 * 1024 * 1024)
    logger.info(f"Starting {molecule_id} with memory limit {memory_limit_gb}GB")
    
    try:
        # Start the process
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        pid = proc.pid
        
        while proc.poll() is None:
            # Process is still running
            current_rss = monitor_memory_usage(pid)
            
            if current_rss is not None:
                if current_rss > limit_bytes:
                    logger.warning(f"Memory limit exceeded for {molecule_id}. RSS: {current_rss/1e9:.2f}GB")
                    handle_oom(molecule_id, pid=pid, skip=True)
                    return None, False, f"Skipped {molecule_id} due to OOM (limit: {memory_limit_gb}GB)"
            
            time.sleep(check_interval)
        
        # Process finished
        stdout, stderr = proc.communicate()
        
        # Check for OOM in stderr/stdout even if process finished (e.g. killed by OOM killer)
        if check_oom_in_log(stdout + stderr):
            handle_oom(molecule_id, pid=pid, skip=True)
            return None, False, f"Skipped {molecule_id} due to OOM detected in log."
        
        # Check for convergence failure
        if detect_convergence_failure(stdout + stderr):
            # Create a temporary log path for error handling context if needed
            # In a real pipeline, we might write to a file first
            handle_convergence_failure(molecule_id, log_path=None, skip=True)
            return proc, False, f"Skipped {molecule_id} due to convergence failure."

        return proc, True, "Success"

    except Exception as e:
        logger.error(f"Exception running {molecule_id}: {e}")
        return None, False, str(e)