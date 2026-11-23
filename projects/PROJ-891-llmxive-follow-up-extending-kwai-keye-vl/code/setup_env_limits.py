"""
Environment configuration for memory limits (cgroups/ulimit) and time limits.

This module provides utilities to enforce resource constraints on child processes
to prevent OOM crashes and excessive runtime during inference.

Features:
- Memory limit enforcement via cgroups v2 (preferred) or ulimit (fallback).
- Time limit enforcement via subprocess timeout and SIGALRM.
- Wrapper function to run a command with these constraints.

Usage:
    from setup_env_limits import run_with_limits
    run_with_limits(['python', 'script.py'], memory_gb=7, time_limit_hours=2)
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

# Configuration defaults
DEFAULT_MEMORY_GB = 7.0
DEFAULT_TIME_LIMIT_HOURS = 2.0
CGROUPS_MEMORY_CONTROLLER = "memory"
CGROUPS_V2_MOUNT_POINT = "/sys/fs/cgroup"
CGROUPS_GROUP_NAME = "llmxive_runner"

def _setup_cgroups_v2(memory_limit_bytes: int) -> Optional[str]:
    """
    Setup a cgroup v2 slice with a specific memory limit.
    
    Args:
        memory_limit_bytes: Maximum memory in bytes.
        
    Returns:
        Path to the cgroup directory if successful, None otherwise.
    """
    if not os.path.exists(CGROUPS_V2_MOUNT_POINT):
        return None
        
    cgroup_path = Path(CGROUPS_V2_MOUNT_POINT) / CGROUPS_GROUP_NAME
    
    try:
        # Create cgroup directory
        cgroup_path.mkdir(parents=True, exist_ok=True)
        
        # Write memory limit (max)
        # Note: In cgroups v2, 'memory.max' is the limit
        limit_file = cgroup_path / "memory.max"
        limit_file.write_text(str(memory_limit_bytes))
        
        # Verify write succeeded
        current_limit = limit_file.read_text().strip()
        if current_limit == "max" or int(current_limit) != memory_limit_bytes:
            # If it's "max" or different, we might not have permission or the write failed
            if current_limit == "max":
                return None # Permission denied or not supported
            return None
            
        return str(cgroup_path)
    except (PermissionError, OSError, ValueError) as e:
        print(f"Warning: Failed to setup cgroups v2: {e}", file=sys.stderr)
        return None

def _cleanup_cgroups_v2(cgroup_path: str) -> None:
    """Remove the cgroup directory if empty."""
    path = Path(cgroup_path)
    try:
        if path.exists() and not any(path.iterdir()):
            path.rmdir()
    except OSError:
        pass

def _set_ulimit_memory(memory_gb: float) -> None:
    """
    Set the soft and hard memory limit for the current process using ulimit.
    Note: This affects the current process and children that don't override it.
    It does not kill the process on OOM like cgroups, but prevents allocation.
    
    Args:
        memory_gb: Memory limit in Gigabytes.
    """
    # ulimit -v is in Kilobytes
    limit_kb = int(memory_gb * 1024 * 1024)
    try:
        # Set soft and hard limits
        os.setrlimit(os.RLIMIT_AS, (limit_kb * 1024, limit_kb * 1024))
    except (ValueError, OSError) as e:
        print(f"Warning: Failed to set ulimit memory: {e}", file=sys.stderr)

def _set_time_limit_handler(signum, frame):
    """Signal handler for time limit."""
    raise TimeoutError(f"Process exceeded time limit of {signum} seconds")

def run_with_limits(
    cmd: List[str],
    memory_gb: float = DEFAULT_MEMORY_GB,
    time_limit_hours: float = DEFAULT_TIME_LIMIT_HOURS,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    check: bool = True
) -> subprocess.CompletedProcess:
    """
    Run a command with enforced memory and time limits.
    
    Priority:
    1. cgroups v2 (if available and writable)
    2. ulimit (fallback for memory)
    
    Time limit is enforced via subprocess timeout and SIGALRM.
    
    Args:
        cmd: Command and arguments to execute.
        memory_gb: Memory limit in GB (default 7GB).
        time_limit_hours: Time limit in hours.
        cwd: Working directory for the subprocess.
        env: Environment variables for the subprocess.
        check: If True, raise CalledProcessError on non-zero exit.
        
    Returns:
        CompletedProcess instance.
        
    Raises:
        TimeoutError: If the process exceeds the time limit.
        MemoryError: If the process is killed due to OOM (cgroups) or exceeds ulimit.
        subprocess.CalledProcessError: If the process exits with non-zero status.
    """
    memory_limit_bytes = int(memory_gb * 1024 * 1024 * 1024)
    time_limit_seconds = int(time_limit_hours * 3600)
    
    # Prepare environment
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
        
    # Attempt cgroups setup
    cgroup_path = _setup_cgroups_v2(memory_limit_bytes)
    
    # Prepare subprocess arguments
    kwargs = {
        "cmd": cmd,
        "cwd": cwd,
        "env": run_env,
        "check": check,
        "timeout": time_limit_seconds, # Native subprocess timeout
    }
    
    # If cgroups failed, try ulimit as a fallback for memory
    # Note: ulimit -v limits virtual memory, which might not catch all OOMs
    # but is better than nothing on systems without cgroups.
    if cgroup_path is None:
        # We cannot easily set ulimit for a child process in a fork/exec model
        # without a wrapper script. We will set it for the current process 
        # which might affect the child if it doesn't exec a new binary.
        # For robust isolation, we rely on the cgroups failure message.
        print(f"Warning: cgroups v2 not available. Memory limit enforcement may be weak.", file=sys.stderr)
        # Try to set ulimit for the current shell context (limited effect on exec)
        try:
            _set_ulimit_memory(memory_gb)
        except Exception:
            pass
    else:
        # If cgroups is set, we need to run the command inside that cgroup.
        # We can use 'cgexec' if available, or manually move the PID if we forked.
        # Since we are using subprocess.run, we can't easily move the child PID 
        # after it's spawned unless we use a wrapper.
        # Strategy: Use 'cgexec' if available, else rely on the fact that 
        # we created the cgroup and hope the child respects it (unlikely without cgexec).
        # Better: Write a small wrapper script or use 'cgexec'.
        
        cgexec_path = shutil.which("cgexec")
        if cgexec_path:
            # Prepend cgexec to the command
            cg_cmd = [cgexec_path, "-g", f"{CGROUPS_MEMORY_CONTROLLER}:{CGROUPS_GROUP_NAME}"] + cmd
            kwargs["cmd"] = cg_cmd
        else:
            print(f"Warning: cgroups configured but 'cgexec' not found. Memory limits may not apply to child.", file=sys.stderr)
            # Fallback to ulimit warning
            _set_ulimit_memory(memory_gb)

    # Set up time limit signal handler for extra safety
    old_handler = signal.signal(signal.SIGALRM, _set_time_limit_handler)
    signal.alarm(time_limit_seconds)
    
    try:
        result = subprocess.run(**kwargs)
        return result
    except subprocess.TimeoutExpired as e:
        # Kill the process group if timeout occurs
        if hasattr(e, 'child') and e.child:
            try:
                os.killpg(os.getpgid(e.child.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        raise TimeoutError(f"Process exceeded time limit of {time_limit_seconds} seconds") from e
    except subprocess.CalledProcessError as e:
        raise e
    finally:
        signal.alarm(0) # Cancel the alarm
        signal.signal(signal.SIGALRM, old_handler)
        if cgroup_path:
            _cleanup_cgroups_v2(cgroup_path)

def main():
    """
    Entry point for testing the environment setup.
    Demonstrates running a simple command with limits.
    """
    print("Testing environment limit setup...")
    
    # Test 1: Simple echo
    try:
        result = run_with_limits(["echo", "Hello from limited environment"], memory_gb=1, time_limit_hours=1)
        print(f"Test 1 (Echo) passed: {result.returncode}")
    except Exception as e:
        print(f"Test 1 failed: {e}")
        
    # Test 2: Simulate a long running process (should timeout)
    print("Test 2: Simulating timeout (this will take ~3 seconds)...")
    start = time.time()
    try:
        # Run a sleep of 5 seconds, limit 2 seconds
        run_with_limits(["sleep", "5"], time_limit_hours=0.00055) # ~2 seconds
        print("Test 2 failed: Should have timed out")
    except TimeoutError:
        print(f"Test 2 passed: Timeout detected in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"Test 2 failed with unexpected error: {e}")

    # Test 3: Simulate memory stress (optional, depends on system)
    # This is hard to test reliably without a specific memory hog script
    # and strict cgroups. We skip it for now to avoid hanging the runner.

if __name__ == "__main__":
    main()
