"""
Resource Monitor Watchdog for Training Processes.

Implements a subprocess wrapper that polls a training process ID (PID)
using psutil. If RAM usage exceeds 7.0 GB or Disk usage exceeds 14.0 GB,
the training process is terminated.

Logs status updates to data/artifacts/resource_monitor.log.
"""
import os
import sys
import time
import json
import signal
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import psutil
except ImportError:
    print("ERROR: psutil is required. Install with: pip install psutil", file=sys.stderr)
    sys.exit(1)

# Constants matching project constraints
RAM_LIMIT_GB = 7.0
DISK_LIMIT_GB = 14.0
POLL_INTERVAL_SECONDS = 5.0
ARTIFACTS_DIR = Path("data/artifacts")
LOG_FILE_PATH = ARTIFACTS_DIR / "resource_monitor.log"

def log_message(message: str, status: str = "info") -> None:
    """
    Write a timestamped JSON log entry to the resource monitor log file.
    """
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "status": status,
        "message": message
    }
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def get_process_memory_gb(process: psutil.Process) -> float:
    """
    Get the Resident Set Size (RSS) of the process in GB.
    """
    try:
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0.0

def get_process_disk_gb(process: psutil.Process) -> float:
    """
    Estimate disk usage of the process by summing sizes of open files.
    Note: This is an estimate and may not capture all disk usage (e.g., tmpfs,
    files opened by child processes not tracked directly).
    """
    total_disk = 0.0
    try:
        # Get open files and their sizes
        for file_path in process.open_files():
            try:
                stat = os.stat(file_path.path)
                total_disk += stat.st_size
            except (OSError, FileNotFoundError):
                continue
        # Add size of memory-mapped files if available (Linux specific)
        if hasattr(process, 'memory_maps'):
            for mmap in process.memory_maps(grouped=True):
                if hasattr(mmap, 'size'):
                    total_disk += mmap.size
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    
    return total_disk / (1024 ** 3)

def check_and_terminate(pid: int) -> bool:
    """
    Check resource usage for the given PID.
    Returns True if the process was terminated due to resource limits.
    Returns False if the process is still running within limits or does not exist.
    """
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        # Process has already exited naturally
        log_message(f"Process {pid} has exited.", "info")
        return False
    except psutil.AccessDenied:
        log_message(f"Access denied to process {pid}.", "error")
        return False

    # Check Memory
    mem_gb = get_process_memory_gb(process)
    if mem_gb > RAM_LIMIT_GB:
        log_message(
            f"RAM limit exceeded: {mem_gb:.2f} GB > {RAM_LIMIT_GB} GB. Terminating PID {pid}.",
            "resource_exceeded"
        )
        try:
            process.terminate() # Send SIGTERM
            # Wait briefly for graceful shutdown
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            log_message(f"Graceful shutdown failed. Sending SIGKILL to PID {pid}.", "resource_exceeded")
            process.kill() # Send SIGKILL
        except psutil.NoSuchProcess:
            pass # Already gone
        
        log_message(f"Process {pid} terminated due to resource limits.", "resource_exceeded")
        return True

    # Check Disk (Process specific estimate)
    disk_gb = get_process_disk_gb(process)
    if disk_gb > DISK_LIMIT_GB:
        log_message(
            f"Disk limit exceeded: {disk_gb:.2f} GB > {DISK_LIMIT_GB} GB. Terminating PID {pid}.",
            "resource_exceeded"
        )
        try:
            process.terminate()
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            process.kill()
        except psutil.NoSuchProcess:
            pass
        
        log_message(f"Process {pid} terminated due to resource limits.", "resource_exceeded")
        return True

    # Normal status check
    log_message(f"PID {pid} OK: RAM={mem_gb:.2f}GB, DiskEst={disk_gb:.2f}GB", "ok")
    return False

def run_watchdog(pid: int, timeout_seconds: Optional[float] = None) -> int:
    """
    Main watchdog loop. Polls the process until it exits, is terminated,
    or the timeout is reached.
    
    Returns:
        0: Process completed normally within limits.
        1: Process terminated due to resource limits or timeout.
    """
    log_message(f"Watchdog started for PID {pid}", "info")
    start_time = time.time()

    while True:
        current_time = time.time()
        
        # Check timeout
        if timeout_seconds is not None:
            elapsed = current_time - start_time
            if elapsed > timeout_seconds:
                log_message(f"Watchdog timeout reached ({elapsed:.1f}s). Terminating PID {pid}.", "timeout")
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    process.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    try:
                        process.kill()
                    except psutil.NoSuchProcess:
                        pass
                return 1

        # Check resources
        if check_and_terminate(pid):
            return 1

        # Check if process is still alive
        try:
            process = psutil.Process(pid)
            if not process.is_running():
                log_message(f"Process {pid} exited naturally.", "info")
                return 0
        except psutil.NoSuchProcess:
            log_message(f"Process {pid} not found.", "info")
            return 0

        time.sleep(POLL_INTERVAL_SECONDS)

def main():
    parser = argparse.ArgumentParser(description="Resource Monitor Watchdog")
    parser.add_argument(
        "pid",
        type=int,
        help="Process ID (PID) of the training process to monitor"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Maximum time in seconds to monitor before killing the process (optional)"
    )
    
    args = parser.parse_args()
    
    exit_code = run_watchdog(args.pid, args.timeout)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
