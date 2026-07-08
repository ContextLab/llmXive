"""
Error handling utilities for quantum chemistry pipelines.

Handles convergence failures (skip/log) and Out-of-Memory (OOM) detection
as per spec.md Edge Cases.
"""

import logging
import os
import re
import signal
import subprocess
import sys
import resource
from typing import Callable, Optional, Tuple, List, Dict, Any
from pathlib import Path

# Configure logging for this module
logger = logging.getLogger(__name__)


class ConvergenceError(Exception):
    """Raised when a quantum calculation fails to converge."""
    pass


class OOMError(Exception):
    """Raised when a process exceeds memory limits."""
    pass


def detect_convergence_failure(log_content: str) -> Tuple[bool, Optional[str]]:
    """
    Detects convergence failures in quantum chemistry log output.

    Checks for common failure patterns in DFTB+ and similar software logs.

    Args:
        log_content: The string content of the calculation log file.

    Returns:
        A tuple (is_failed, failure_reason).
        is_failed: True if a convergence failure is detected.
        failure_reason: A string describing the failure, or None if no failure found.
    """
    # Common patterns for convergence failures
    failure_patterns = [
        r"convergence\s+not\s+achieved",
        r"failed\s+to\s+converge",
        r"maximum\s+iterations\s+exceeded",
        r"no\s+convergence\s+after",
        r"calculation\s+aborted",
        r"error:\s+convergence",
        r"scf\s+did\s+not\s+converge",
        r"electronic\s+convergence\s+failed",
    ]

    log_lower = log_content.lower()

    for pattern in failure_patterns:
        if re.search(pattern, log_lower, re.IGNORECASE):
            # Extract a snippet around the match for better logging
            match = re.search(pattern, log_lower)
            if match:
                start = max(0, match.start() - 50)
                end = min(len(log_content), match.end() + 50)
                snippet = log_content[start:end].replace('\n', ' ')
                return True, f"Convergence failure detected: {snippet}"

    return False, None


def check_oom_in_log(log_content: str) -> Tuple[bool, Optional[str]]:
    """
    Checks log content for Out-of-Memory (OOM) killer messages.

    Args:
        log_content: The string content of the log file.

    Returns:
        A tuple (is_oom, oom_reason).
    """
    oom_patterns = [
        r"out\s*of\s*memory",
        r"oom",
        r"killed\s+by\s+oom",
        r"memory\s+allocation\s+failed",
        r"cannot\s+allocate\s+memory",
        r"exceeded\s+memory\s+limit",
        r"segmentation\s+fault.*memory",
    ]

    log_lower = log_content.lower()

    for pattern in oom_patterns:
        if re.search(pattern, log_lower, re.IGNORECASE):
            return True, "Out of memory condition detected in log"

    return False, None


def handle_convergence_failure(
    molecule_id: str,
    error_message: str,
    log_path: Optional[str] = None,
    skip_file_path: Optional[str] = None
) -> None:
    """
    Handles a convergence failure by logging it and optionally recording it
    in a skip file.

    Args:
        molecule_id: Identifier for the molecule that failed.
        error_message: The specific error message.
        log_path: Path to the log file (for context).
        skip_file_path: Path to a file where failed molecule IDs should be recorded.
    """
    logger.warning(f"Convergence failure for molecule {molecule_id}: {error_message}")
    if log_path:
        logger.warning(f"Log file: {log_path}")

    if skip_file_path:
        skip_file = Path(skip_file_path)
        skip_file.parent.mkdir(parents=True, exist_ok=True)
        with open(skip_file, 'a') as f:
            f.write(f"{molecule_id}\t{error_message}\n")
        logger.info(f"Recorded failure for {molecule_id} in {skip_file_path}")


def handle_oom(
    molecule_id: str,
    suggested_action: Optional[str] = None
) -> None:
    """
    Handles an Out-of-Memory error by logging it and generating a user-facing suggestion.

    Args:
        molecule_id: Identifier for the molecule that caused OOM.
        suggested_action: A custom suggestion string. If None, a default one is generated.
    """
    if suggested_action is None:
        suggested_action = (
            "OOM detected. Consider reducing the subset size of molecules processed "
            "in a single run, or increasing available system memory. "
            "For DFTB+/Psi4, try reducing the number of parallel threads or "
            "using a smaller basis set if applicable."
        )

    logger.error(f"Out of Memory (OOM) for molecule {molecule_id}")
    logger.error(f"Suggested action: {suggested_action}")
    raise OOMError(f"Process killed due to OOM for molecule {molecule_id}. {suggested_action}")


def monitor_memory_usage(
    threshold_gb: float = 6.5,
    process: Optional[subprocess.Popen] = None
) -> bool:
    """
    Monitors the memory usage of a subprocess or the current process.

    Args:
        threshold_gb: Memory threshold in GB. Default 6.5GB as per spec.
        process: Optional subprocess.Popen object to monitor. If None, monitors current process.

    Returns:
        True if memory usage exceeds threshold, False otherwise.
    """
    try:
        if process is not None:
            # Check if process is still running
            if process.poll() is not None:
                return False
            pid = process.pid
        else:
            pid = os.getpid()

        # Read memory status from /proc on Linux
        if sys.platform == 'linux':
            with open(f'/proc/{pid}/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        rss_kb = int(line.split()[1])
                        rss_gb = rss_kb / (1024 * 1024)
                        if rss_gb > threshold_gb:
                            return True
        else:
            # Fallback for non-Linux systems (less accurate)
            try:
                import resource
                usage = resource.getrusage(resource.RUSAGE_SELF)
                rss_mb = usage.ru_maxrss
                # On macOS, ru_maxrss is in bytes; on Linux, it's in KB
                if sys.platform == 'darwin':
                    rss_gb = rss_mb / (1024 * 1024 * 1024)
                else:
                    rss_gb = rss_mb / (1024 * 1024)

                if rss_gb > threshold_gb:
                    return True
            except Exception:
                logger.warning("Could not determine memory usage on non-Linux platform")
                return False

    except Exception as e:
        logger.warning(f"Failed to monitor memory: {e}")
        return False

    return False


def run_with_oom_protection(
    cmd: List[str],
    molecule_id: str,
    timeout_seconds: Optional[int] = None,
    memory_threshold_gb: float = 6.5,
    check_interval_seconds: float = 1.0
) -> Tuple[Optional[subprocess.CompletedProcess], Optional[str]]:
    """
    Runs a subprocess with OOM protection.

    Monitors the process memory usage and kills it if it exceeds the threshold.

    Args:
        cmd: Command to run as a list of strings.
        molecule_id: Identifier for the molecule being processed.
        timeout_seconds: Optional timeout for the process.
        memory_threshold_gb: Memory threshold in GB.
        check_interval_seconds: Interval between memory checks.

    Returns:
        A tuple (result, error_message).
        result: CompletedProcess if successful, None if OOM or timeout.
        error_message: Error description if failed, None if successful.
    """
    import time
    import threading

    process = None
    oom_detected = False
    timed_out = False

    def memory_monitor():
        nonlocal oom_detected, process
        while process is not None and process.poll() is None:
            if monitor_memory_usage(threshold_gb=memory_threshold_gb, process=process):
                oom_detected = True
                logger.error(f"Memory threshold exceeded for {molecule_id}. Killing process.")
                try:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                except Exception as e:
                    logger.error(f"Failed to kill process: {e}")
                break
            time.sleep(check_interval_seconds)

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Start memory monitor thread
        monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
        monitor_thread.start()

        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            if oom_detected:
                handle_oom(molecule_id)
                return None, "Process killed due to OOM"
            return subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr), None

        except subprocess.TimeoutExpired:
            process.kill()
            timed_out = True
            return None, f"Process timed out after {timeout_seconds} seconds"

    except Exception as e:
        return None, f"Exception during process execution: {str(e)}"
    finally:
        if process and process.poll() is None:
            process.kill()