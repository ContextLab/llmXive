"""
Memory monitoring utilities for subprocess management.

Uses the Python `resource` module to monitor Resident Set Size (RSS)
of spawned processes and kill them if they exceed a defined threshold.
"""
import logging
import os
import resource
import signal
import subprocess
import sys
from typing import Callable, Optional, Any

# Threshold in bytes (6.5 GB)
MEMORY_LIMIT_BYTES = 6.5 * 1024**3
MEMORY_LIMIT_GB = 6.5

logger = logging.getLogger(__name__)


class MemoryLimitExceededError(RuntimeError):
    """Raised when a subprocess exceeds the memory limit."""
    pass


def get_current_process_rss_bytes() -> int:
    """
    Returns the current process RSS in bytes.
    
    Note: This measures the current process, not a child.
    For child monitoring, we rely on periodic checks in the runner.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, bytes on macOS.
    # To be safe, we check the platform.
    if sys.platform == 'darwin':
        return usage.ru_maxrss
    else:
        return usage.ru_maxrss * 1024


def check_process_memory(pid: int, limit_bytes: int = MEMORY_LIMIT_BYTES) -> bool:
    """
    Check if a process with given PID exceeds the memory limit.
    
    Returns True if the process is using more memory than the limit.
    Returns False if within limit or if the process cannot be checked.
    """
    try:
        # On Linux, read /proc/<pid>/status
        if sys.platform.startswith('linux'):
            status_path = f"/proc/{pid}/status"
            if not os.path.exists(status_path):
                return False
            
            with open(status_path, 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # Format: "VmRSS:     12345 kB"
                        parts = line.split()
                        if len(parts) >= 2:
                            rss_kb = int(parts[1])
                            rss_bytes = rss_kb * 1024
                            return rss_bytes > limit_bytes
        
        # Fallback for other platforms (less precise or unavailable)
        # We cannot accurately check child RSS on non-Linux without specific tools
        logger.warning(f"Cannot check memory for PID {pid} on {sys.platform}.")
        return False
        
    except (ValueError, PermissionError, FileNotFoundError) as e:
        logger.debug(f"Could not check memory for PID {pid}: {e}")
        return False


def kill_process(pid: int) -> None:
    """
    Forcefully kill a process and its children.
    """
    try:
        # Send SIGKILL to the process group if possible, otherwise just the PID
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except ProcessLookupError:
        logger.debug(f"Process {pid} already terminated.")
    except Exception as e:
        logger.error(f"Failed to kill process {pid}: {e}")
        # Fallback to single kill
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass


def generate_oom_suggestion(subset_size: Optional[int] = None) -> str:
    """
    Generate a user-facing suggestion string upon OOM detection.
    
    Args:
        subset_size: The number of molecules currently being processed.
                    If provided, suggests a smaller number.
    
    Returns:
        A formatted suggestion string.
    """
    suggestion = (
        f"Out of Memory (OOM) detected. The process exceeded {MEMORY_LIMIT_GB}GB of RAM.\n"
        "DFTB+ calculations can be memory-intensive, especially with large basis sets or many atoms.\n\n"
        "Recommendations:\n"
        "1. Reduce the subset size of molecules being processed in a single run.\n"
    )
    
    if subset_size and subset_size > 1:
        suggested_size = max(1, int(subset_size * 0.5))
        suggestion += f"   - Try processing a smaller batch (e.g., {suggested_size} molecules instead of {subset_size}).\n"
    
    suggestion += (
        "2. Check if your system has sufficient swap space enabled.\n"
        "3. Close other memory-intensive applications.\n"
        "4. If running on a cluster, request a node with more RAM.\n"
    )
    
    return suggestion


def run_with_memory_limit(
    cmd: list,
    memory_limit_bytes: int = MEMORY_LIMIT_BYTES,
    check_interval: float = 1.0,
    timeout: Optional[float] = None,
    subset_size: Optional[int] = None
) -> subprocess.CompletedProcess:
    """
    Run a subprocess with a memory limit.
    
    If the process exceeds `memory_limit_bytes`, it is killed and a
    MemoryLimitExceededError is raised with a user suggestion.
    
    Args:
        cmd: Command and arguments to run.
        memory_limit_bytes: Maximum allowed RSS in bytes.
        check_interval: Seconds between memory checks.
        timeout: Maximum runtime for the process (optional).
        subset_size: Number of items processed, used for OOM suggestion.
    
    Returns:
        CompletedProcess instance if successful.
    
    Raises:
        MemoryLimitExceededError: If memory limit is exceeded.
        subprocess.TimeoutExpired: If timeout is reached.
        subprocess.SubprocessError: If the process fails for other reasons.
    """
    import time
    import threading

    logger.info(f"Starting process: {' '.join(cmd)}")
    logger.info(f"Memory limit set to {memory_limit_bytes / (1024**3):.2f} GB")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # Create new process group for killing children
    )

    pid = process.pid
    memory_exceeded_event = threading.Event()
    error_msg = None

    def monitor_loop():
        nonlocal error_msg
        start_time = time.time()
        
        while process.poll() is None:  # While process is running
            if time.time() - start_time > (timeout or float('inf')):
                break
            
            if check_process_memory(pid, memory_limit_bytes):
                logger.error(f"Memory limit exceeded for PID {pid}")
                kill_process(pid)
                memory_exceeded_event.set()
                error_msg = generate_oom_suggestion(subset_size)
                break
            
            time.sleep(check_interval)

    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()

    try:
        stdout, stderr = process.communicate(timeout=timeout)
        monitor_thread.join(timeout=1) # Ensure monitor thread finishes
        
        if memory_exceeded_event.is_set():
            raise MemoryLimitExceededError(error_msg)
        
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )

    except subprocess.TimeoutExpired:
        kill_process(pid)
        raise
    except KeyboardInterrupt:
        kill_process(pid)
        raise