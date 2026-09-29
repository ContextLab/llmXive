"""
Resource constraint wrapper for the analysis pipeline.

Monitors CPU and RAM usage using psutil. If thresholds are exceeded,
logs a warning and terminates the current analysis process after a grace period.
"""
import os
import sys
import time
import signal
import subprocess
import threading
import logging
import json
from pathlib import Path
from datetime import datetime

try:
    import psutil
except ImportError:
    raise ImportError(
        "psutil is required for resource_guard. "
        "Install it via: pip install psutil"
    )


class ResourceGuardError(Exception):
    """Raised when resource limits are exceeded and a process is terminated."""
    pass


# Configuration defaults (can be overridden via environment or config)
DEFAULT_CPU_THRESHOLD = 2.0  # cores
DEFAULT_RAM_THRESHOLD = 7.0  # GB
DEFAULT_GRACE_PERIOD = 30.0  # seconds
DEFAULT_LOG_PATH = "data/logs/pipeline.log"


def _get_process_info(pid=None):
    """Get CPU and RAM info for a specific process or the current one."""
    if pid is None:
        pid = os.getpid()
    
    try:
        process = psutil.Process(pid)
        cpu_percent = process.cpu_percent()
        ram_info = process.memory_info()
        ram_gb = ram_info.rss / (1024 ** 3)
        return cpu_percent, ram_gb
    except psutil.NoSuchProcess:
        return 0.0, 0.0


def _log_resource_event(message, level="WARNING"):
    """Log resource events to the pipeline log file in JSON Lines format."""
    log_path = Path(DEFAULT_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "component": "resource_guard",
        "message": message,
        "pid": os.getpid()
    }
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Also print to stderr for immediate visibility
    if level == "ERROR" or level == "WARNING":
        print(f"[{level}] {message}", file=sys.stderr)


def _monitor_resources(cpu_threshold, ram_threshold, grace_period):
    """
    Monitor CPU and RAM usage in a background thread.
    
    If thresholds are exceeded, logs a warning and waits for the grace period.
    If the condition persists, it raises ResourceGuardError to trigger termination.
    """
    start_time = time.time()
    exceeded_start = None
    
    while True:
        cpu_percent, ram_gb = _get_process_info()
        
        # Check if thresholds are exceeded
        is_cpu_exceeded = cpu_percent > (cpu_threshold * 100)  # psutil returns 0-100 per core
        is_ram_exceeded = ram_gb > ram_threshold
        
        if is_cpu_exceeded or is_ram_exceeded:
            if exceeded_start is None:
                exceeded_start = time.time()
                _log_resource_event(
                    f"Resource threshold exceeded: CPU={cpu_percent:.1f}% (limit={cpu_threshold*100:.1f}%), "
                    f"RAM={ram_gb:.2f}GB (limit={ram_threshold}GB). Grace period started.",
                    "WARNING"
                )
            else:
                elapsed = time.time() - exceeded_start
                if elapsed >= grace_period:
                    _log_resource_event(
                        f"Grace period ({grace_period}s) expired. Terminating process. "
                        f"Final stats: CPU={cpu_percent:.1f}%, RAM={ram_gb:.2f}GB",
                        "ERROR"
                    )
                    raise ResourceGuardError(
                        f"Resource limits exceeded for {elapsed:.1f}s. "
                        f"CPU: {cpu_percent:.1f}%, RAM: {ram_gb:.2f}GB"
                    )
        else:
            exceeded_start = None
        
        # Sleep for a short interval to avoid busy-waiting
        time.sleep(1.0)


def run_with_limits(
    cpu_threshold=DEFAULT_CPU_THRESHOLD,
    ram_threshold=DEFAULT_RAM_THRESHOLD,
    grace_period=DEFAULT_GRACE_PERIOD,
    target_function=None,
    *args,
    **kwargs
):
    """
    Run a target function with resource monitoring.
    
    If resource limits are exceeded, the function is interrupted and
    a ResourceGuardError is raised.
    
    Args:
        cpu_threshold: Max CPU cores allowed (e.g., 2.0)
        ram_threshold: Max RAM in GB allowed (e.g., 7.0)
        grace_period: Seconds to wait before terminating after threshold breach
        target_function: The function to run under guard
        *args, **kwargs: Arguments to pass to target_function
        
    Returns:
        The return value of target_function if it completes successfully.
        
    Raises:
        ResourceGuardError: If resource limits are exceeded.
    """
    if target_function is None:
        raise ValueError("target_function must be provided")
    
    # Start the monitoring thread
    monitor_thread = threading.Thread(
        target=_monitor_resources,
        args=(cpu_threshold, ram_threshold, grace_period),
        daemon=True
    )
    monitor_thread.start()
    
    try:
        result = target_function(*args, **kwargs)
        return result
    except ResourceGuardError:
        # Re-raise the guard error
        raise
    except Exception as e:
        # Log unexpected errors but don't suppress them
        _log_resource_event(f"Unexpected error in guarded function: {str(e)}", "ERROR")
        raise


def run_command_with_limits(
    cmd,
    cpu_threshold=DEFAULT_CPU_THRESHOLD,
    ram_threshold=DEFAULT_RAM_THRESHOLD,
    grace_period=DEFAULT_GRACE_PERIOD,
    **subprocess_kwargs
):
    """
    Run a shell command with resource monitoring.
    
    If resource limits are exceeded, the command process is terminated with SIGKILL.
    
    Args:
        cmd: Command to run (string or list)
        cpu_threshold: Max CPU cores allowed
        ram_threshold: Max RAM in GB allowed
        grace_period: Seconds to wait before terminating
        **subprocess_kwargs: Additional kwargs for subprocess.run
        
    Returns:
        subprocess.CompletedProcess instance
        
    Raises:
        ResourceGuardError: If resource limits are exceeded and process is terminated.
    """
    # Convert string command to list if necessary
    if isinstance(cmd, str):
        cmd_list = cmd.split()
    else:
        cmd_list = list(cmd)
    
    # Start the target process
    process = subprocess.Popen(
        cmd_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **subprocess_kwargs
    )
    
    # Store the process ID for monitoring
    target_pid = process.pid
    
    # Override _get_process_info to monitor the target process
    original_get_info = _get_process_info
    
    def _get_target_info(pid=None):
        if pid is None:
            return original_get_info(target_pid)
        return original_get_info(pid)
    
    # Patch temporarily
    import resource_guard
    resource_guard._get_process_info = _get_target_info
    
    # Start monitoring thread
    monitor_thread = threading.Thread(
        target=_monitor_resources,
        args=(cpu_threshold, ram_threshold, grace_period),
        daemon=True
    )
    monitor_thread.start()
    
    try:
        # Wait for the process to complete
        stdout, stderr = process.communicate()
        return subprocess.CompletedProcess(
            process.args,
            process.returncode,
            stdout,
            stderr
        )
    except ResourceGuardError as e:
        # Terminate the target process with SIGKILL
        _log_resource_event(f"Terminating process {target_pid} due to resource limits", "ERROR")
        try:
            process.kill()  # SIGKILL
            process.wait()
        except Exception:
            pass
        raise ResourceGuardError(
            f"Command terminated due to resource limits: {str(e)}"
        ) from e
    finally:
        # Restore original function
        resource_guard._get_process_info = original_get_info


def main():
    """
    Entry point for command-line usage.
    
    Usage:
        python resource_guard.py <command> [args...]
        
    Example:
        python resource_guard.py python analysis_script.py
    """
    if len(sys.argv) < 2:
        print("Usage: python resource_guard.py <command> [args...]", file=sys.stderr)
        print("Example: python resource_guard.py python script.py", file=sys.stderr)
        sys.exit(1)
    
    # Parse thresholds from environment or use defaults
    cpu_threshold = float(os.environ.get("RESOURCE_GUARD_CPU", DEFAULT_CPU_THRESHOLD))
    ram_threshold = float(os.environ.get("RESOURCE_GUARD_RAM", DEFAULT_RAM_THRESHOLD))
    grace_period = float(os.environ.get("RESOURCE_GUARD_GRACE", DEFAULT_GRACE_PERIOD))
    
    # Build command
    cmd = sys.argv[1:]
    
    _log_resource_event(
        f"Starting resource-guarded command: {' '.join(cmd)}. "
        f"Thresholds: CPU={cpu_threshold} cores, RAM={ram_threshold}GB, "
        f"Grace={grace_period}s",
        "INFO"
    )
    
    try:
        result = run_command_with_limits(
            cmd,
            cpu_threshold=cpu_threshold,
            ram_threshold=ram_threshold,
            grace_period=grace_period
        )
        sys.exit(result.returncode)
    except ResourceGuardError as e:
        _log_resource_event(f"Process terminated: {str(e)}", "ERROR")
        # Exit with code 137 (128 + 9 for SIGKILL)
        sys.exit(137)


if __name__ == "__main__":
    main()