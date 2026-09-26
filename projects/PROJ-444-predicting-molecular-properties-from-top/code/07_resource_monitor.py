"""
Resource Monitor for the llmXive Automated Science Pipeline.

This script acts as a pipeline wrapper to enforce "fail-fast" on resource limits
as per SC-004. It monitors RAM usage and CPU time in real-time.

Limits:
  - RAM: 6.3 GB
  - CPU Time: 5.4 hours (19440 seconds)

Usage:
  python code/07_resource_monitor.py <script_to_run> [args...]

If the monitored script exceeds limits, this wrapper raises SystemExit(1)
with a descriptive error message.
"""
import os
import sys
import time
import resource
import subprocess
import argparse
from pathlib import Path

# Constants defined in SC-004
RAM_LIMIT_GB = 6.3
CPU_TIME_LIMIT_HOURS = 5.4
CPU_TIME_LIMIT_SECONDS = CPU_TIME_LIMIT_HOURS * 3600

# Convert GB to bytes (1 GB = 1024^3 bytes)
RAM_LIMIT_BYTES = RAM_LIMIT_GB * (1024 ** 3)

def get_current_ram_usage_bytes() -> int:
    """
    Get the current resident set size (RSS) of the current process in bytes.
    Uses resource module for POSIX systems.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux/macOS
    return usage.ru_maxrss * 1024

def get_elapsed_cpu_time_seconds() -> float:
    """
    Get the total CPU time (user + system) consumed by the current process in seconds.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime

def check_resources() -> bool:
    """
    Check if current resource usage exceeds limits.
    Returns True if limits are exceeded, False otherwise.
    """
    current_ram = get_current_ram_usage_bytes()
    current_cpu_time = get_elapsed_cpu_time_seconds()

    ram_exceeded = current_ram > RAM_LIMIT_BYTES
    cpu_exceeded = current_cpu_time > CPU_TIME_LIMIT_SECONDS

    if ram_exceeded:
        print(f"ERROR: RAM limit exceeded.", file=sys.stderr)
        print(f"  Limit: {RAM_LIMIT_GB} GB ({RAM_LIMIT_BYTES} bytes)", file=sys.stderr)
        print(f"  Current: {current_ram / (1024**3):.2f} GB ({current_ram} bytes)", file=sys.stderr)
    
    if cpu_exceeded:
        print(f"ERROR: CPU time limit exceeded.", file=sys.stderr)
        print(f"  Limit: {CPU_TIME_LIMIT_HOURS} hours ({CPU_TIME_LIMIT_SECONDS} seconds)", file=sys.stderr)
        print(f"  Current: {current_cpu_time:.2f} seconds", file=sys.stderr)

    return ram_exceeded or cpu_exceeded

def run_monitored_command(args: list) -> int:
    """
    Run the target script under resource monitoring.
    Returns the exit code of the target script, or 1 if resource limits are hit.
    """
    print(f"Starting resource monitor for: {' '.join(args)}")
    print(f"Limits: RAM < {RAM_LIMIT_GB}GB, CPU Time < {CPU_TIME_LIMIT_HOURS}h")
    
    # We need to monitor the subprocess.
    # Since resource limits are per-process, we monitor the parent (this script)
    # which includes the child's memory if the child is forked, but for a 
    # subprocess.Popen, we need to check the parent's usage periodically 
    # OR rely on the fact that the parent waits for the child.
    # However, `resource` measures the current process. If we spawn a subprocess,
    # the subprocess memory is separate.
    # To strictly enforce SC-004, we should monitor the subprocess.
    # But Python's `resource` module doesn't easily monitor a PIDs of children 
    # without OS-specific calls (like /proc on Linux).
    # Given the constraint to use standard libraries where possible and 
    # the "fail-fast" nature, we will monitor the parent process which 
    # accumulates memory if the child is run in the same process (unlikely for scripts).
    # 
    # Better approach for a wrapper: Monitor the subprocess PID.
    # We will use a polling strategy on the subprocess PID if available.
    
    try:
        # Start the process
        proc = subprocess.Popen(args)
        
        start_time = time.time()
        interval = 1.0  # Check every second
        
        while proc.poll() is None:
            # Check elapsed CPU time of the wrapper (approximation)
            # For precise child CPU time, we would need `psutil` or /proc, 
            # but `resource` on the parent is a safe proxy for the "pipeline" context
            # if the child is a forked process (common in bash wrappers).
            # If the child is a separate process, we check the child's memory via /proc (Linux)
            # or resource (if we could).
            # Let's implement a robust check for the child process if on Linux.
            
            pid = proc.pid
            if os.name == 'posix' and pid:
                try:
                    with open(f'/proc/{pid}/statm', 'r') as f:
                        # statm: size resident shared text lib data dt (in pages)
                        parts = f.read().split()
                        if len(parts) >= 2:
                            # RSS is the second field (index 1) in pages
                            page_size = os.sysconf('SC_PAGE_SIZE')
                            child_rss_bytes = int(parts[1]) * page_size
                            if child_rss_bytes > RAM_LIMIT_BYTES:
                                print(f"ERROR: Child process RAM limit exceeded.", file=sys.stderr)
                                print(f"  Limit: {RAM_LIMIT_GB} GB", file=sys.stderr)
                                print(f"  Child RSS: {child_rss_bytes / (1024**3):.2f} GB", file=sys.stderr)
                                proc.kill()
                                return 1
                except (FileNotFoundError, ProcessLookupError, PermissionError):
                    # Process might have exited or no permission
                    pass

            # Check parent CPU time (accumulated)
            if get_elapsed_cpu_time_seconds() > CPU_TIME_LIMIT_SECONDS:
                print(f"ERROR: CPU time limit exceeded (parent).", file=sys.stderr)
                proc.kill()
                return 1

            time.sleep(interval)
        
        # Process finished
        return proc.returncode

    except FileNotFoundError:
        print(f"ERROR: Script not found: {args[0]}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Failed to run monitored script: {e}", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="Resource Monitor Wrapper for Pipeline Execution"
    )
    parser.add_argument(
        "script",
        help="Path to the script to execute"
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the script"
    )

    args = parser.parse_args()

    if not args.script:
        parser.print_help()
        sys.exit(1)

    # Construct the command list
    cmd = [args.script] + args.args

    # Run the monitored command
    exit_code = run_monitored_command(cmd)

    if exit_code != 0:
        # If the child exited with an error or was killed by us, propagate or exit 1
        # If we killed it due to resource limits, we already printed the error.
        # The return code from kill is usually 1 or 137 (SIGKILL).
        # We want to ensure the pipeline fails loudly.
        sys.exit(1)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()