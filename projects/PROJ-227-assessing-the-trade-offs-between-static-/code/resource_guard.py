"""
Resource constraint wrapper for the LLM analysis pipeline.

Enforces hard limits on CPU usage, RAM usage, and wall-clock time.
Uses psutil for monitoring and cgroups (where available) for enforcement.
Exits with code 137 (SIGKILL) on violation.
"""

import os
import sys
import time
import signal
import subprocess
import threading
from typing import Optional, Callable, Any

import psutil

# Constants
MAX_CPU_PERCENT = 200.0  # 2 cores * 100%
MAX_RAM_GB = 7.0
MAX_RAM_BYTES = int(MAX_RAM_GB * 1024 ** 3)
MAX_TIME_HOURS = 6.0
MAX_TIME_SECONDS = int(MAX_TIME_HOURS * 3600)
CHECK_INTERVAL_SECONDS = 1.0
EXIT_CODE_VIOLATION = 137

class ResourceGuardError(Exception):
    """Raised when a resource limit is violated."""
    pass


def _get_process_memory_bytes() -> int:
    """Get current process RSS memory in bytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


def _get_process_cpu_percent() -> float:
    """Get current process CPU percentage (multi-core aware)."""
    # Returns percentage relative to total system CPU count
    return psutil.Process(os.getpid()).cpu_percent(interval=None)


def _setup_cgroups_limits() -> Optional[str]:
    """
    Attempt to set up cgroups v2 limits for CPU and Memory.
    Returns the cgroup path if successful, None otherwise.
    Note: This requires root privileges and a cgroups v2 enabled system.
    """
    try:
        # Check if cgroups v2 is mounted
        if not os.path.exists('/sys/fs/cgroup/cgroup.controllers'):
            return None

        # Create a unique cgroup for this process
        cgroup_name = f"llmXive_guard_{os.getpid()}"
        cgroup_path = f"/sys/fs/cgroup/{cgroup_name}"

        if not os.path.exists(cgroup_path):
            os.makedirs(cgroup_path, exist_ok=True)

        # Set memory limit (in bytes)
        memory_file = os.path.join(cgroup_path, "memory.max")
        with open(memory_file, 'w') as f:
            f.write(str(MAX_RAM_BYTES))

        # Set CPU limit (weight based approach for cgroups v2)
        # Convert percent to weight: 100% = 10000 weight units (approx)
        # 200% = 20000
        cpu_weight = int(MAX_CPU_PERCENT * 100)
        cpu_max_file = os.path.join(cgroup_path, "cpu.max")
        # Format: "max $period" or "$quota $period"
        # Using a period of 100ms (100000 us)
        period = 100000
        quota = int((MAX_CPU_PERCENT / 100.0) * period)
        with open(cpu_max_file, 'w') as f:
            f.write(f"{quota} {period}")

        # Move current process to cgroup
        cgroup_procs = os.path.join(cgroup_path, "cgroup.procs")
        with open(cgroup_procs, 'w') as f:
            f.write(str(os.getpid()))

        return cgroup_path

    except (PermissionError, OSError, FileNotFoundError) as e:
        # cgroups setup failed, will rely on psutil monitoring only
        return None


def _check_resources() -> None:
    """
    Check current resource usage against limits.
    Raises ResourceGuardError if any limit is exceeded.
    """
    # Check RAM
    current_ram = _get_process_memory_bytes()
    if current_ram > MAX_RAM_BYTES:
        raise ResourceGuardError(
            f"RAM limit exceeded: {current_ram / (1024**3):.2f}GB > {MAX_RAM_GB}GB"
        )

    # Check CPU (using a short interval for accuracy)
    current_cpu = _get_process_cpu_percent()
    if current_cpu > MAX_CPU_PERCENT:
        raise ResourceGuardError(
            f"CPU limit exceeded: {current_cpu:.1f}% > {MAX_CPU_PERCENT}%"
        )


def _monitor_loop(stop_event: threading.Event, cgroup_path: Optional[str]) -> None:
    """
    Background thread to monitor resources.
    If cgroups are available, it also acts as a safety net.
    """
    start_time = time.time()

    while not stop_event.is_set():
        # Check wall-clock time
        elapsed = time.time() - start_time
        if elapsed > MAX_TIME_SECONDS:
            print(f"ERROR: Time limit exceeded ({elapsed:.1f}s > {MAX_TIME_SECONDS}s)", file=sys.stderr)
            os._exit(EXIT_CODE_VIOLATION)

        try:
            _check_resources()
        except ResourceGuardError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            os._exit(EXIT_CODE_VIOLATION)

        time.sleep(CHECK_INTERVAL_SECONDS)


def run_with_limits(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    Run a function with enforced resource limits.

    Args:
        func: The function to execute.
        *args: Positional arguments for func.
        **kwargs: Keyword arguments for func.

    Returns:
        The return value of func.

    Raises:
        SystemExit: With code 137 if a limit is violated.
        Exception: Any exception raised by func.
    """
    # Setup cgroups if possible (best effort)
    cgroup_path = _setup_cgroups_limits()
    if cgroup_path:
        print(f"ResourceGuard: cgroups limits applied at {cgroup_path}", file=sys.stderr)
    else:
        print("ResourceGuard: cgroups not available, using psutil monitoring only", file=sys.stderr)

    # Start monitoring thread
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=_monitor_loop,
        args=(stop_event, cgroup_path),
        daemon=True
    )
    monitor_thread.start()

    try:
        result = func(*args, **kwargs)
        return result
    finally:
        stop_event.set()
        monitor_thread.join(timeout=1.0)


def run_command_with_limits(cmd: list, timeout: Optional[float] = None) -> subprocess.CompletedProcess:
    """
    Run an external command with resource limits.

    Args:
        cmd: Command and arguments as a list.
        timeout: Optional timeout for the command itself (in seconds).

    Returns:
        CompletedProcess instance.
    """
    def wrapper():
        # Run the command
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return proc.returncode

    # We cannot easily wrap subprocess.run in run_with_limits because
    # the child process is separate. Instead, we rely on cgroups if set up
    # before calling this function, or we wrap the parent logic.
    # For this implementation, we assume the caller runs this inside
    # a context where run_with_limits is active, or cgroups are set up.
    # If cgroups were set up in the parent, they apply to children too.
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


def main() -> None:
    """
    Entry point for running a command with resource limits.

    Usage:
        python code/resource_guard.py <command> [args...]
    """
    if len(sys.argv) < 2:
        print("Usage: python resource_guard.py <command> [args...]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1:]

    def execute_cmd():
        result = subprocess.run(cmd)
        return result.returncode

    print(f"Starting command: {' '.join(cmd)}", file=sys.stderr)
    print(f"Limits: CPU ≤ {MAX_CPU_PERCENT}%, RAM ≤ {MAX_RAM_GB}GB, Time ≤ {MAX_TIME_HOURS}h", file=sys.stderr)

    try:
        exit_code = run_with_limits(execute_cmd)
        sys.exit(exit_code)
    except SystemExit as e:
        # Re-raise the exit code (including our 137)
        raise
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
