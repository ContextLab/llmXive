import hashlib
import json
import logging
import os
import resource
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Resource limit constants
MAX_MEMORY_GB = 14.0
MAX_CPU_HOURS = 2.0
MEMORY_WARNING_THRESHOLD = 0.9
CPU_WARNING_THRESHOLD = 0.8

class ResourceLimitExceeded(Exception):
    """Raised when a resource limit is exceeded."""
    pass

class ResourceWarning(Exception):
    """Raised when a resource usage is approaching a limit."""
    pass

def detect_resources() -> Tuple[int, float]:
    """Detect available CPU cores and memory in GB."""
    try:
        cpu_count = os.cpu_count() or 1
    except Exception:
        cpu_count = 1

    try:
        # Get memory info from /proc/meminfo on Linux or fallback
        if os.path.exists('/proc/meminfo'):
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        parts = line.split()
                        # Value is in kB
                        mem_kb = int(parts[1])
                        mem_gb = mem_kb / (1024 * 1024)
                        return cpu_count, mem_gb
        # Fallback: use resource module (Unix)
        mem_limit = resource.getrlimit(resource.RLIMIT_AS)[0]
        if mem_limit != resource.RLIM_INFINITY and mem_limit != -1:
            return cpu_count, mem_limit / (1024 ** 3)
        return cpu_count, 8.0  # Conservative default
    except Exception:
        return cpu_count, 8.0

def calculate_caps() -> Dict[str, Any]:
    """Calculate resource caps based on detection."""
    cpu_count, mem_gb = detect_resources()
    return {
        'cpu_count': cpu_count,
        'memory_gb': mem_gb,
        'max_memory_gb': min(mem_gb, MAX_MEMORY_GB),
        'max_cpu_hours': MAX_CPU_HOURS,
        'memory_warning_threshold': MEMORY_WARNING_THRESHOLD,
        'cpu_warning_threshold': CPU_WARNING_THRESHOLD,
    }

def get_cpu_usage_hours() -> float:
    """Get current CPU usage in hours since process start."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_utime + ru_stime in seconds
    total_seconds = usage.ru_utime + usage.ru_stime
    return total_seconds / 3600.0

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, MB on macOS
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)
    return usage.ru_maxrss / (1024 * 1024)

def check_limits() -> Optional[ResourceLimitExceeded]:
    """Check if resource limits are exceeded."""
    caps = calculate_caps()
    mem_gb = get_memory_usage_gb()
    cpu_hours = get_cpu_usage_hours()

    if mem_gb > caps['max_memory_gb']:
        return ResourceLimitExceeded(
            f"Memory usage {mem_gb:.2f}GB exceeds limit {caps['max_memory_gb']:.2f}GB"
        )
    if cpu_hours > caps['max_cpu_hours']:
        return ResourceLimitExceeded(
            f"CPU usage {cpu_hours:.2f}h exceeds limit {caps['max_cpu_hours']:.2f}h"
        )
    return None

def resource_monitor() -> None:
    """Monitor resources and raise warning or error if limits approached/exceeded."""
    caps = calculate_caps()
    mem_gb = get_memory_usage_gb()
    cpu_hours = get_cpu_usage_hours()

    if mem_gb > caps['max_memory_gb'] * caps['memory_warning_threshold']:
        logging.warning(f"Memory usage approaching limit: {mem_gb:.2f}GB / {caps['max_memory_gb']:.2f}GB")
    if cpu_hours > caps['max_cpu_hours'] * caps['cpu_warning_threshold']:
        logging.warning(f"CPU usage approaching limit: {cpu_hours:.2f}h / {caps['max_cpu_hours']:.2f}h")

    error = check_limits()
    if error:
        raise error

def enforce_resource_limits() -> None:
    """Set hard resource limits via resource module."""
    caps = calculate_caps()
    # Set memory limit (RLIMIT_AS)
    mem_bytes = int(caps['max_memory_gb'] * 1024 ** 3)
    try:
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except ValueError as e:
        logging.warning(f"Could not set memory limit: {e}")

    # Set CPU time limit
    cpu_seconds = int(caps['max_cpu_hours'] * 3600)
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    except ValueError as e:
        logging.warning(f"Could not set CPU limit: {e}")

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_docker_run_flags() -> Dict[str, Any]:
    """Get Docker run flags for resource limits."""
    caps = calculate_caps()
    return {
        'memory': f"{int(caps['max_memory_gb'])}g",
        'cpus': caps['cpu_count'],
    }

def ensure_docker_limits() -> None:
    """Ensure Docker limits are set correctly."""
    # This is a no-op in Python, but provides a hook for validation
    caps = calculate_caps()
    logging.info(f"Docker limits: {caps['max_memory_gb']}GB memory, {caps['cpu_count']} CPUs")

def generate_watchdog_script(output_path: str) -> None:
    """Generate a watchdog script to monitor resource usage."""
    script_content = f"""#!/bin/bash
# Watchdog script for resource monitoring
# Generated at: {__import__('datetime').datetime.now().isoformat()}

MAX_MEMORY_GB={calculate_caps()['max_memory_gb']}
MAX_CPU_HOURS={calculate_caps()['max_cpu_hours']}

monitor_resources() {{
    while true; do
  MEM_USAGE=$(ps -o rss= -p $$ | awk '{{print $1/1024/1024}}')
  CPU_TIME=$(ps -o etime= -p $$ | awk -F: '{{print $1*3600+$2*60+$3}}')
  CPU_HOURS=$(echo "$CPU_TIME / 3600" | bc -l)

  if (( $(echo "$MEM_USAGE > $MAX_MEMORY_GB" | bc -l) )); then
      echo "WARNING: Memory usage $MEM_USAGE GB exceeds limit $MAX_MEMORY_GB GB"
  fi

  if (( $(echo "$CPU_HOURS > $MAX_CPU_HOURS" | bc -l) )); then
      echo "WARNING: CPU usage $CPU_HOURS h exceeds limit $MAX_CPU_HOURS h"
      kill -9 $$
  fi

  sleep 10
    done
}}

monitor_resources &
WATCHDOG_PID=$!

# Run the main process
exec "$@"

# Cleanup
kill $WATCHDOG_PID 2>/dev/null
"""
    Path(output_path).write_text(script_content)
    os.chmod(output_path, 0o755)

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger('llmXive')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(file_handler)

    return logger

def main() -> None:
    """Main entry point for utility functions."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    caps = calculate_caps()
    logger.info(f"Detected resources: {caps['cpu_count']} CPUs, {caps['memory_gb']:.2f}GB memory")
    logger.info(f"Resource caps: {caps['max_memory_gb']:.2f}GB memory, {caps['max_cpu_hours']:.2f}h CPU")

    # Test checksum
    test_file = '/tmp/test_checksum.txt'
    Path(test_file).write_text('test content')
    checksum = calculate_checksum(test_file)
    logger.info(f"Test checksum for {test_file}: {checksum}")

    # Test resource monitoring
    resource_monitor()
    logger.info("Resource monitoring passed")

    # Generate watchdog script
    watchdog_path = '/tmp/watchdog.sh'
    generate_watchdog_script(watchdog_path)
    logger.info(f"Generated watchdog script at {watchdog_path}")

    Path(test_file).unlink()
    Path(watchdog_path).unlink()

    logger.info("All utility tests passed")

if __name__ == '__main__':
    main()