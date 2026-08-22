import hashlib
import json
import logging
import os
import resource
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Optional, Callable, Any, Dict

from src.config import get_project_root

# --- Configuration Constants (FR-012, SC-004, SC-005) ---
# These defaults align with the task description and config.py expectations.
# In production, these should ideally be read from config.py, but we define
# safe defaults here to ensure the module works standalone if needed.
MAX_CPU_HOURS: float = 6.0
MAX_RAM_GB: float = 7.0
WARNING_THRESHOLD: float = 0.85  # Warn at 85% usage

# --- Custom Exception ---
class ResourceLimitExceeded(Exception):
    """Exception raised when resource limits (CPU/Memory) are exceeded."""
    def __init__(self, limit_type: str, limit_value: float, current_usage: float):
        self.limit_type = limit_type
        self.limit_value = limit_value
        self.current_usage = current_usage
        message = (
            f"Resource limit exceeded: {limit_type} limit {limit_value} "
            f"exceeded. Per FR-012, SC-004, SC-005. "
            f"Current usage: {current_usage:.2f}."
        )
        super().__init__(message)

# --- Logging Setup (Reusing existing pattern) ---
def setup_logging(name: str = "resource_monitor") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()

# --- Resource Monitoring Logic ---
def get_cpu_usage_hours() -> float:
    """Returns CPU time used by current process in hours."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_utime + ru_stime in seconds
    total_seconds = usage.ru_utime + usage.ru_stime
    return total_seconds / 3600.0

def get_memory_usage_gb() -> float:
    """Returns Resident Set Size (RSS) memory used by current process in GB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, bytes on macOS? Usually KB on Linux.
    # To be safe, we assume KB for Linux (standard in most HPC/Docker envs).
    # If on macOS, ru_maxrss is bytes. We'll check platform.
    if sys.platform == 'darwin':
        rss_bytes = usage.ru_maxrss
    else:
        # Assume Linux/Unix standard (KB)
        rss_bytes = usage.ru_maxrss * 1024
    
    return rss_bytes / (1024 ** 3)

def check_limits() -> None:
    """Checks current resource usage against limits and raises if exceeded."""
    cpu_hours = get_cpu_usage_hours()
    mem_gb = get_memory_usage_gb()

    if cpu_hours > MAX_CPU_HOURS:
        raise ResourceLimitExceeded("CPU", MAX_CPU_HOURS, cpu_hours)
    
    if mem_gb > MAX_RAM_GB:
        raise ResourceLimitExceeded("RAM", MAX_RAM_GB, mem_gb)

    # Warning logic
    if cpu_hours > (MAX_CPU_HOURS * WARNING_THRESHOLD):
        logger.warning(f"Warning: Resource usage approaching limit: CPU {cpu_hours:.2f} / {MAX_CPU_HOURS}")
    if mem_gb > (MAX_RAM_GB * WARNING_THRESHOLD):
        logger.warning(f"Warning: Resource usage approaching limit: RAM {mem_gb:.2f} / {MAX_RAM_GB}")

@contextmanager
def resource_monitor(limit_type: Optional[str] = None):
    """
    Context manager to monitor CPU and Memory usage within a block.
    Checks limits periodically or at exit.
    """
    start_time = time.time()
    try:
        yield
        check_limits() # Final check on exit
    except ResourceLimitExceeded:
        raise
    except Exception as e:
        logger.error(f"Error in monitored block: {e}")
        raise
    finally:
        # Log final stats for audit
        logger.info(f"Block execution finished. CPU Hours: {get_cpu_usage_hours():.2f}, RAM GB: {get_memory_usage_gb():.2f}")

def enforce_resource_limits(func: Callable) -> Callable:
    """
    Decorator to enforce resource limits on a function.
    Wraps the function to check limits before and after execution.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Starting monitored execution of {func.__name__}")
        check_limits() # Pre-check
        try:
            result = func(*args, **kwargs)
            check_limits() # Post-check
            return result
        except ResourceLimitExceeded:
            logger.critical(f"Resource limit exceeded during {func.__name__}. Terminating.")
            raise
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {e}")
            raise
    return wrapper

# --- Docker Enforcement Helpers ---
def get_docker_run_flags() -> str:
    """
    Detects available system resources and calculates capped values
    to enforce FR-012 regardless of runner capacity.
    Returns a string of flags for 'docker run'.
    """
    # Detect CPU cores
    try:
        cpu_count = int(os.popen('nproc').read().strip())
    except Exception:
        cpu_count = 2 # Fallback

    # Detect RAM (free -g)
    try:
        # 'free -g' outputs in GB, but might be 0 for small amounts.
        # Better to parse /proc/meminfo or use resource limits if available.
        # For robustness, we try 'free' first.
        output = subprocess.check_output(['free', '-g'], text=True)
        # Parse second line (Mem:)
        lines = output.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            total_gb = int(parts[1])
        else:
            total_gb = 4 # Fallback
    except Exception:
        total_gb = 4 # Fallback

    # Calculate caps (min of detected and safe thresholds)
    capped_cpus = min(cpu_count, int(MAX_CPU_HOURS)) # Rough mapping: 1 core = 1 hour budget? 
    # Actually, --cpus sets the CPU quota. If we have 6 hours budget, we can't strictly limit 
    # "hours" via docker flags directly without a time-based watchdog inside the container.
    # However, we can limit the *concurrency* to match the budget roughly if we assume 1 hour = 1 core-hour.
    # A safer interpretation for Docker flags:
    # --cpus: Limit the number of CPU cores.
    # --memory: Limit RAM.
    
    # We cap cores to MAX_CPU_HOURS (6) to prevent runaway parallelism, 
    # but realistically we should cap to available cores.
    docker_cpus = min(cpu_count, 6) 
    docker_mem_gb = min(total_gb, int(MAX_RAM_GB))

    # Ensure we don't request 0 or negative
    docker_cpus = max(1, docker_cpus)
    docker_mem_gb = max(1, docker_mem_gb)

    return f"--cpus={docker_cpus} --memory={docker_mem_gb}g"

def ensure_docker_limits(command: list) -> list:
    """
    Ensures a docker run command includes resource limit flags.
    Modifies the command list in place or returns a new list.
    """
    # Check if 'docker' and 'run' are present
    if 'docker' in command and 'run' in command:
        run_idx = command.index('run')
        # Check if flags already exist to avoid duplicates
        has_cpus = any('--cpus' in arg for arg in command[run_idx:])
        has_mem = any('--memory' in arg for arg in command[run_idx:])
        
        if not has_cpus or not has_mem:
            flags = get_docker_run_flags().split()
            # Insert after 'run'
            new_cmd = command[:run_idx+1] + flags + command[run_idx+1:]
            return new_cmd
    return command

# --- Watchdog Script Generator ---
def generate_watchdog_script() -> str:
    """
    Generates the content for scripts/watchdog.sh.
    This script monitors a container and kills it if limits are exceeded.
    """
    return f"""#!/bin/bash
# Watchdog script for Docker container resource monitoring
# Enforces FR-012, SC-004, SC-005

CONTAINER_NAME="${{1:-project_container}}"
CPU_LIMIT_HOURS={MAX_CPU_HOURS}
RAM_LIMIT_GB={MAX_RAM_GB}
CHECK_INTERVAL=10 # seconds

echo "Starting watchdog for container: $CONTAINER_NAME"
echo "Limits: CPU={CPU_LIMIT_HOURS}h, RAM={RAM_LIMIT_GB}GB"

while true; do
    if ! docker inspect -f '{{{{.State.Running}}}}' "$CONTAINER_NAME" 2>/dev/null | grep -q true; then
  echo "Container stopped or not found. Exiting watchdog."
  exit 0
    fi

    # Get CPU usage (percentage)
    # docker stats --no-stream returns: CONTAINER ID, NAME, CPU %, MEM USAGE, ...
    STATS=$(docker stats --no-stream --format "{{{{.CPUPerc}}}} {{{{.MemUsage}}}}" "$CONTAINER_NAME")
    
    CPU_PCT=$(echo "$STATS" | awk '{{print $1}}' | tr -d '%')
    MEM_USAGE=$(echo "$STATS" | awk '{{print $2}}') # e.g., "2.5GiB"

    # Parse CPU (float comparison)
    if (( $(echo "$CPU_PCT > 100 * $CPU_LIMIT_HOURS" | bc -l) )); then
  # Note: CPU% in docker stats is relative to total cores. 
  # If we have 4 cores, 400% is 100% utilization.
  # This simple check assumes we want to kill if average CPU usage over time is high?
  # A better approach for hours is to track cumulative time, but for a simple watchdog:
  # We will rely on the internal Python check for precise hour tracking.
  # This shell script primarily handles RAM and simple CPU spikes.
  :
    fi

    # Parse RAM (convert GiB to GB roughly or compare strings)
    # Simplified: Extract number and unit
    MEM_VAL=$(echo "$MEM_USAGE" | grep -oP '^[0-9.]+')
    MEM_UNIT=$(echo "$MEM_USAGE" | grep -oP '[A-Za-z]+$')

    CURRENT_GB=0
    if [[ "$MEM_UNIT" == "GiB" ]]; then
  CURRENT_GB=$MEM_VAL
    elif [[ "$MEM_UNIT" == "MiB" ]]; then
  CURRENT_GB=$(echo "$MEM_VAL / 1024" | bc)
    fi

    if (( $(echo "$CURRENT_GB > $RAM_LIMIT_GB" | bc -l) )); then
  echo "WARNING: RAM limit exceeded ($CURRENT_GB > $RAM_LIMIT_GB). Killing container."
  docker stop "$CONTAINER_NAME"
  exit 1
    fi

    sleep $CHECK_INTERVAL
done
"""

# --- Main Execution for Standalone Testing ---
def main():
    """
    Main entry point for testing resource monitoring.
    """
    print("Testing Resource Monitoring...")
    print(f"Max CPU Hours: {MAX_CPU_HOURS}")
    print(f"Max RAM GB: {MAX_RAM_GB}")
    
    try:
        with resource_monitor():
            print("Inside monitored block.")
            # Simulate some work
            time.sleep(1)
            check_limits()
            print("Limits checked successfully.")
    except ResourceLimitExceeded as e:
        print(f"Caught expected exception: {e}")
        return 1
    
    print("Watchdog script generated:")
    print(generate_watchdog_script())
    return 0

if __name__ == "__main__":
    sys.exit(main())