"""
DFTB+ Execution Logging Module for PROJ-546.

Implements logging and timing for DFTB+ invocations as per Task T017.
Captures molecule_id, command, exit_code, duration, and peak_memory_mb
to logs/dftb_execution.log in JSON format.
"""
import json
import logging
import os
import resource
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DFTB_LOG_PATH = LOGS_DIR / "dftb_execution.log"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_peak_memory_mb() -> float:
    """
    Retrieve the peak memory usage of the current process in MB.
    Uses resource.getrusage on Unix-like systems.
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux/macOS
        peak_kb = usage.ru_maxrss
        return float(peak_kb) / 1024.0
    except AttributeError:
        # Fallback for non-Unix systems (though DFTB+ is typically Unix)
        return 0.0

def log_dftb_invocation(
    molecule_id: str,
    command: str,
    exit_code: int,
    duration: float,
    peak_memory_mb: float,
    log_file: Optional[Path] = None
) -> None:
    """
    Append a single DFTB+ invocation record to the JSON log file.

    Args:
        molecule_id: Unique identifier for the molecule.
        command: The shell command executed.
        exit_code: Exit code returned by the process.
        duration: Execution time in seconds.
        peak_memory_mb: Peak memory usage in MB.
        log_file: Optional path to log file (defaults to DFTB_LOG_PATH).
    """
    record = {
        "molecule_id": molecule_id,
        "command": command,
        "exit_code": exit_code,
        "duration": round(duration, 4),
        "peak_memory_mb": round(peak_memory_mb, 2),
        "timestamp": datetime.utcnow().isoformat()
    }

    target_path = log_file or DFTB_LOG_PATH

    # Append as JSON Lines (one JSON object per line) for easy parsing
    with open(target_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def finalize_dftb_log(log_file: Optional[Path] = None) -> None:
    """
    Finalize the log file by writing a summary footer or closing handles.
    Currently, since we use append mode with JSONL, this is a no-op
    but provided for API completeness.
    """
    pass

def log_dftb_invocation_jsonl(
    records: List[Dict[str, Any]],
    log_file: Optional[Path] = None
) -> None:
    """
    Bulk write multiple DFTB+ invocation records to the log file.

    Args:
        records: List of dictionaries matching the schema.
        log_file: Optional path to log file.
    """
    target_path = log_file or DFTB_LOG_PATH
    with open(target_path, "a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

def timed_dftb_run(
    molecule_id: str,
    command: List[str],
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a DFTB+ command with timing and memory tracking.

    Args:
        molecule_id: Unique identifier for the molecule.
        command: List of arguments for subprocess.run.
        timeout: Optional timeout in seconds.

    Returns:
        Dictionary containing execution details.
    """
    start_time = time.time()
    start_mem = get_peak_memory_mb()
    exit_code = -1
    command_str = " ".join(command)

    try:
        # Run the DFTB+ process
        # Note: We assume DFTB+ is installed and in PATH or specified in command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        exit_code = -1  # Or specific timeout code
    except FileNotFoundError:
        exit_code = 127  # Standard shell error for command not found
    except Exception as e:
        exit_code = -1
        # Log the exception to stderr or a separate error log if needed
        logging.error(f"Error running DFTB+ for {molecule_id}: {e}")
    finally:
        end_time = time.time()
        duration = end_time - start_time
        # Get peak memory after execution
        peak_memory_mb = get_peak_memory_mb()
        # Ensure we capture the max if it increased during run
        # Note: get_peak_memory_mb() returns the max for the process lifetime so far

        record = {
            "molecule_id": molecule_id,
            "command": command_str,
            "exit_code": exit_code,
            "duration": duration,
            "peak_memory_mb": peak_memory_mb
        }

        log_dftb_invocation(
            molecule_id=molecule_id,
            command=command_str,
            exit_code=exit_code,
            duration=duration,
            peak_memory_mb=peak_memory_mb
        )

        return record

def main() -> None:
    """
    Entry point for testing the logging module independently.
    Writes a sample entry to verify the log file creation and format.
    """
    print("Testing DFTB+ logging module...")
    test_record = {
        "molecule_id": "TEST-001",
        "command": "dftb+ --help",
        "exit_code": 0,
        "duration": 0.05,
        "peak_memory_mb": 15.2
    }
    log_dftb_invocation_jsonl([test_record])
    print(f"Sample log entry written to {DFTB_LOG_PATH}")
    print("Verification: Check logs/dftb_execution.log for JSON content.")

if __name__ == "__main__":
    main()