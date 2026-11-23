import json
import logging
import os
import resource
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Log file path as defined in tasks.md
LOG_FILE_PATH = "logs/dft_execution.log"

def get_peak_memory_mb() -> float:
    """
    Returns the peak memory usage of the current process in MB.
    Uses resource.getrusage on Unix-like systems.
    On Windows, this returns 0.0 as resource is not available.
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux/macOS
        peak_kb = usage.ru_maxrss
        return peak_kb / 1024.0
    except Exception:
        # Fallback for systems where resource.getrusage is not supported or fails
        return 0.0

def log_dftb_invocation(
    molecule_id: str,
    command: str,
    exit_code: int,
    duration: float,
    peak_memory_mb: float,
    log_path: Optional[str] = None
) -> None:
    """
    Appends a single JSON line to the DFTB execution log.
    
    Args:
        molecule_id: Unique identifier for the molecule.
        command: The shell command string executed.
        exit_code: The integer exit code returned by the process.
        duration: Execution time in seconds (float).
        peak_memory_mb: Peak memory usage in MB (float).
        log_path: Optional override for the log file path. Defaults to LOG_FILE_PATH.
    """
    if log_path is None:
        log_path = LOG_FILE_PATH
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    entry = {
        "molecule_id": molecule_id,
        "command": command,
        "exit_code": exit_code,
        "duration": duration,
        "peak_memory_mb": peak_memory_mb
    }
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def log_dftb_invocation_jsonl(
    entries: list,
    log_path: Optional[str] = None
) -> None:
    """
    Appends multiple log entries to the DFTB execution log.
    
    Args:
        entries: List of dictionaries containing log data.
        log_path: Optional override for the log file path.
    """
    if log_path is None:
        log_path = LOG_FILE_PATH
        
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        
    with open(log_path, "a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

def timed_dftb_run(
    molecule_id: str,
    command: str,
    log_path: Optional[str] = None
) -> tuple:
    """
    Runs a DFTB+ command, times it, monitors memory, and logs the result.
    
    This function wraps subprocess execution to capture duration and peak memory,
    then writes the structured log entry.
    
    Args:
        molecule_id: Unique identifier for the molecule.
        command: The shell command string to execute.
        log_path: Optional override for the log file path.
        
    Returns:
        tuple: (exit_code, duration, peak_memory_mb)
    """
    if log_path is None:
        log_path = LOG_FILE_PATH
        
    start_time = time.time()
    peak_memory_mb = 0.0
    exit_code = -1
    
    try:
        # Reset resource usage stats before running if possible (Unix only)
        try:
            resource.setrlimit(resource.RUSAGE_SELF, resource.getrlimit(resource.RUSAGE_SELF))
        except (AttributeError, ValueError):
            pass
            
        process = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        exit_code = process.returncode
        
        # Get peak memory after execution
        peak_memory_mb = get_peak_memory_mb()
        
    except Exception as e:
        logging.error(f"Error running DFTB+ for {molecule_id}: {e}")
        exit_code = -1
        
    finally:
        duration = time.time() - start_time
        
        # Log the invocation
        log_dftb_invocation(
            molecule_id=molecule_id,
            command=command,
            exit_code=exit_code,
            duration=duration,
            peak_memory_mb=peak_memory_mb,
            log_path=log_path
        )
        
    return exit_code, duration, peak_memory_mb

def finalize_dftb_log(log_path: Optional[str] = None) -> None:
    """
    Finalizes the log file, e.g., by adding a footer or closing handles.
    Currently a placeholder for future extensibility.
    """
    if log_path is None:
        log_path = LOG_FILE_PATH
        
    if os.path.exists(log_path):
        # Could add a summary line or metadata here in the future
        pass

def main():
    """
    Main entry point for testing the logging utility directly.
    """
    test_molecule_id = "TEST_MOL_001"
    test_command = "echo 'Simulating DFTB+ run for testing'"
    
    logging.basicConfig(level=logging.INFO)
    
    print(f"Running test for molecule: {test_molecule_id}")
    exit_code, duration, peak_mem = timed_dftb_run(
        molecule_id=test_molecule_id,
        command=test_command
    )
    
    print(f"Test completed. Exit code: {exit_code}, Duration: {duration:.4f}s, Peak Memory: {peak_mem:.2f}MB")
    print(f"Log written to: {LOG_FILE_PATH}")

if __name__ == "__main__":
    main()