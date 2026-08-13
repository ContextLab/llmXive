"""
Error handling utilities for molecular property prediction pipeline.

This module provides tools to handle convergence failures, OOM detection,
and structural failures in quantum chemical calculations.
"""
import logging
import os
import re
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class ConvergenceError(Exception):
    """Raised when a quantum chemical calculation fails to converge."""
    pass


class OOMError(Exception):
    """Raised when a process exceeds memory limits (OOM)."""
    pass


class StructuralError(Exception):
    """Raised when a calculation produces structurally invalid results (e.g., HOMO >= LUMO)."""
    pass


# Log file paths (relative to project root)
LOGS_DIR = Path("logs")
CONVERGENCE_LOG = LOGS_DIR / "convergence_failures.log"
OOM_LOG = LOGS_DIR / "oom_failures.log"
STRUCTURAL_LOG = LOGS_DIR / "structural_failures.log"


def _ensure_log_dir():
    """Ensure the logs directory exists."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _write_log_entry(log_path: Path, entry: Dict[str, Any]):
    """
    Write a log entry to the specified log file in CSV format.
    
    Args:
        log_path: Path to the log file.
        entry: Dictionary containing log fields.
    """
    _ensure_log_dir()
    file_exists = log_path.exists()
    
    with open(log_path, 'a') as f:
        if not file_exists:
            # Write header if file doesn't exist
            f.write(','.join(entry.keys()) + '\n')
        
        # Write values, handling potential commas in messages by quoting
        values = []
        for key in entry.keys():
            val = str(entry.get(key, ''))
            if ',' in val or '"' in val or '\n' in val:
                val = '"' + val.replace('"', '""') + '"'
            values.append(val)
        f.write(','.join(values) + '\n')


def detect_convergence_failure(log_content: str) -> bool:
    """
    Detect convergence failure patterns in DFTB+ or similar output logs.
    
    Args:
        log_content: String content of the calculation log.
        
    Returns:
        True if convergence failure is detected, False otherwise.
    """
    patterns = [
        r'convergence.*not.*reached',
        r'failed.*to.*converge',
        r'convergence.*error',
        r'cycle.*limit.*reached',
        r'scf.*not.*converged',
        r'no.*convergence',
    ]
    
    log_lower = log_content.lower()
    for pattern in patterns:
        if re.search(pattern, log_lower, re.IGNORECASE):
            return True
    return False


def check_oom_in_log(log_content: str) -> bool:
    """
    Detect OOM (Out of Memory) signals in log content.
    
    Args:
        log_content: String content of the calculation log.
        
    Returns:
        True if OOM is detected, False otherwise.
    """
    patterns = [
        r'out.*of.*memory',
        r'oom',
        r'memory.*allocation.*failed',
        r'cannot.*allocate.*memory',
        r'killed',
        r'signal.*9',
        r'signal.*kill',
    ]
    
    log_lower = log_content.lower()
    for pattern in patterns:
        if re.search(pattern, log_lower, re.IGNORECASE):
            return True
    return False


def monitor_memory_usage(pid: Optional[int] = None) -> int:
    """
    Monitor the current process memory usage (RSS) in bytes.
    
    Args:
        pid: Process ID to monitor. If None, monitors current process.
        
    Returns:
        Memory usage in bytes.
    """
    if pid is None:
        pid = os.getpid()
    
    try:
        with open(f'/proc/{pid}/statm', 'r') as f:
            parts = f.read().split()
            # Second field is RSS in pages
            rss_pages = int(parts[1])
            page_size = os.sysconf('SC_PAGE_SIZE')
            return rss_pages * page_size
    except (FileNotFoundError, IndexError, ValueError):
        # Fallback for non-Linux systems or errors
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss * 1024  # Convert KB to bytes
        except Exception:
            return 0


def handle_convergence_failure(
    molecule_id: str,
    error_message: str,
    retry_count: int = 0,
    status: str = "failed_after_retry"
):
    """
    Handle a convergence failure by logging it and raising an exception.
    
    Args:
        molecule_id: Identifier for the molecule being processed.
        error_message: Description of the error.
        retry_count: Number of retries attempted (default 0).
        status: Status string for the log entry.
    """
    timestamp = datetime.utcnow().isoformat()
    entry = {
        "molecule_id": molecule_id,
        "timestamp": timestamp,
        "error_code": "CONVERGENCE_FAILURE",
        "error_message": error_message,
        "status": status
    }
    _write_log_entry(CONVERGENCE_LOG, entry)
    raise ConvergenceError(f"Convergence failure for {molecule_id}: {error_message}")


def handle_oom(
    molecule_id: str,
    error_message: str,
    memory_usage_bytes: int,
    status: str = "failed_after_retry"
):
    """
    Handle an OOM failure by logging it and raising an exception.
    
    Args:
        molecule_id: Identifier for the molecule being processed.
        error_message: Description of the error.
        memory_usage_bytes: Memory usage at the time of failure.
        status: Status string for the log entry.
    """
    timestamp = datetime.utcnow().isoformat()
    entry = {
        "molecule_id": molecule_id,
        "timestamp": timestamp,
        "error_code": "OOM_FAILURE",
        "error_message": error_message,
        "status": status,
        "memory_usage_bytes": memory_usage_bytes
    }
    _write_log_entry(OOM_LOG, entry)
    raise OOMError(f"OOM failure for {molecule_id}: {error_message}")


def handle_structural_failure(
    molecule_id: str,
    error_message: str,
    status: str = "failed_after_retry"
):
    """
    Handle a structural failure (e.g., HOMO >= LUMO) by logging it.
    
    Args:
        molecule_id: Identifier for the molecule being processed.
        error_message: Description of the error.
        status: Status string for the log entry.
    """
    timestamp = datetime.utcnow().isoformat()
    entry = {
        "molecule_id": molecule_id,
        "timestamp": timestamp,
        "error_code": "STRUCTURAL_FAILURE",
        "error_message": error_message,
        "status": status
    }
    _write_log_entry(STRUCTURAL_LOG, entry)
    raise StructuralError(f"Structural failure for {molecule_id}: {error_message}")


def run_with_oom_protection(
    func,
    *args,
    memory_limit_bytes: int = 7 * 1024**3,  # 7 GB default
    molecule_id: str = "unknown",
    **kwargs
):
    """
    Run a function with memory protection, killing the process if it exceeds the limit.
    
    Args:
        func: Function to run.
        *args: Positional arguments for the function.
        memory_limit_bytes: Memory limit in bytes.
        molecule_id: Identifier for logging purposes.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        Result of the function if successful.
        
    Raises:
        OOMError: If memory limit is exceeded.
    """
    import signal
    
    def memory_limit_handler(signum, frame):
        raise OOMError(f"Memory limit exceeded for {molecule_id}")
    
    # Set up signal handler (Unix only)
    old_handler = None
    try:
        old_handler = signal.signal(signal.SIGXCPU, memory_limit_handler)
    except (AttributeError, ValueError):
        # SIGXCPU not available on this platform
        pass
    
    try:
        # Start monitoring memory in a separate thread if possible
        # For simplicity, we'll rely on the process being killed by the OS
        # and catching the signal, or using resource limits
        import resource
        # Set soft and hard limits (in bytes, converted to KB for Unix)
        limit_kb = memory_limit_bytes // 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit_kb, limit_kb))
        
        return func(*args, **kwargs)
    except OOMError:
        raise
    except MemoryError:
        raise OOMError(f"MemoryError caught for {molecule_id}")
    except subprocess.CalledProcessError as e:
        if check_oom_in_log(e.stderr or ""):
            raise OOMError(f"Process killed due to OOM for {molecule_id}: {e.stderr}")
        raise
    finally:
        # Restore old handler
        if old_handler is not None:
            try:
                signal.signal(signal.SIGXCPU, old_handler)
            except (AttributeError, ValueError):
                pass