"""
Resource Monitor for llmXive Pipeline (SC-004 Enforcement).

This module implements a "fail-fast" wrapper for the main pipeline execution.
It monitors RAM usage and CPU time in real-time. If resource limits are exceeded,
it raises SystemExit(1) with a descriptive error message.

Limits (SC-004):
  - Max RAM: 6.3 GB
  - Max CPU Time: 5.4 hours
"""

import os
import sys
import time
import resource
import subprocess
import argparse
import logging
from typing import Callable, List, Optional

# Constants for SC-004
MAX_RAM_GB = 6.3
MAX_CPU_HOURS = 5.4

MAX_RAM_BYTES = MAX_RAM_GB * 1024 * 1024 * 1024
MAX_CPU_SECONDS = MAX_CPU_HOURS * 3600

# Setup logging
LOG_FILE = "data/logs/resource_monitor.log"
os.makedirs("data/logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ResourceMonitor")


def get_current_ram_usage_bytes() -> int:
    """
    Returns the current resident set size (RSS) of the process in bytes.
    Uses the resource module (Unix/Unix-like systems).
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux, bytes on macOS.
    # We normalize to bytes for consistency.
    maxrss_kb = usage.ru_maxrss
    if os.system("uname -s | grep -q Darwin") == 0:
        # macOS: already in bytes
        return maxrss_kb
    else:
        # Linux/Unix: in kilobytes
        return maxrss_kb * 1024


def get_elapsed_cpu_time_seconds() -> float:
    """
    Returns the total CPU time (user + system) used by the process in seconds.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


def check_resources() -> bool:
    """
    Checks current RAM and CPU time against SC-004 limits.

    Returns:
        True if resources are within limits.
        Raises SystemExit(1) if limits are exceeded.
    """
    current_ram = get_current_ram_usage_bytes()
    current_cpu = get_elapsed_cpu_time_seconds()

    if current_ram > MAX_RAM_BYTES:
        ram_gb = current_ram / (1024 ** 3)
        logger.error(f"SC-004 Violation: RAM limit exceeded. Current: {ram_gb:.2f}GB > Limit: {MAX_RAM_GB}GB")
        raise SystemExit(1)

    if current_cpu > MAX_CPU_SECONDS:
        cpu_hours = current_cpu / 3600
        logger.error(f"SC-004 Violation: CPU time limit exceeded. Current: {cpu_hours:.2f}h > Limit: {MAX_CPU_HOURS}h")
        raise SystemExit(1)

    logger.debug(f"Resources OK: RAM={current_ram/(1024**3):.2f}GB, CPU={current_cpu/3600:.2f}h")
    return True


def run_monitored_command(
    command: List[str],
    check_interval: float = 1.0,
    on_interval: Optional[Callable[[], None]] = None
) -> int:
    """
    Runs a subprocess command while monitoring the *parent* process resources.
    If the parent process exceeds limits, it exits immediately.

    Note: This monitors the runner's memory (e.g., the Python script itself).
    For strict subprocess isolation, the subprocess would need its own monitor,
    but SC-004 typically applies to the pipeline runner's footprint.

    Args:
        command: List of arguments for the subprocess.
        check_interval: Seconds between resource checks.
        on_interval: Optional callback to run between checks.

    Returns:
        Exit code of the subprocess if successful, or 1 if resource limits hit.
    """
    logger.info(f"Starting monitored execution: {' '.join(command)}")
    logger.info(f"SC-004 Limits: RAM < {MAX_RAM_GB}GB, CPU < {MAX_CPU_HOURS}h")

    start_time = time.time()
    process = subprocess.Popen(command)

    try:
        while process.poll() is None:
            # Check resources
            check_resources()

            # Optional callback
            if on_interval:
                on_interval()

            # Sleep before next check
            time.sleep(check_interval)

        return process.returncode

    except SystemExit as e:
        logger.warning("Resource limit exceeded. Terminating subprocess...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        raise e


def main():
    """
    Entry point for the resource monitor.
    Parses arguments and runs the specified command.

    Usage:
        python code/07_resource_monitor.py -- python code/02_tda_computation.py
    """
    parser = argparse.ArgumentParser(
        description="Run a command with SC-004 resource monitoring."
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="The command and its arguments to execute."
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Check interval in seconds (default: 1.0)"
    )

    args = parser.parse_args()

    if not args.command:
        logger.error("No command provided to monitor.")
        sys.exit(1)

    try:
        exit_code = run_monitored_command(args.command, check_interval=args.interval)
        logger.info(f"Process completed with exit code: {exit_code}")
        sys.exit(exit_code)
    except SystemExit as e:
        # Re-raise the specific exit code from resource check
        sys.exit(e.code)


if __name__ == "__main__":
    main()