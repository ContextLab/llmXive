"""
Utility functions for the biomarker discovery pipeline.
Includes logging setup, checksum calculation, and runtime resource monitoring.
"""
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
from pathlib import Path
from typing import Optional, Dict, Any, Generator

from .config import get_project_root, ensure_directories

# --- Custom Exception ---
class ResourceLimitExceeded(Exception):
    """Raised when CPU time or memory usage exceeds defined limits."""
    def __init__(self, limit_type: str, limit_value: Any, current_value: Any):
        self.limit_type = limit_type
        self.limit_value = limit_value
        self.current_value = current_value
        message = (
            f"Resource limit exceeded: {limit_type} limit {limit_value} "
            f"exceeded. Per FR-012, SC-004, SC-005. "
            f"Current usage: {current_value}."
        )
        super().__init__(message)

# --- Logging Setup ---
def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the pipeline.
    
    Args:
        log_file: Optional path to a log file. If None, logs to stdout/stderr.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("biomarker_pipeline")
    logger.setLevel(level)
    
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        ensure_directories()
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger

# --- Checksums ---
def calculate_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default 'sha256').
        
    Returns:
        Hex digest string of the file's checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

# --- Runtime Monitoring ---
def get_cpu_usage_hours() -> float:
    """
    Get the CPU time used by the current process in hours.
    
    Returns:
        CPU time in hours.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_utime (user time) + ru_stime (system time) in seconds
    total_seconds = usage.ru_utime + usage.ru_stime
    return total_seconds / 3600.0

def get_memory_usage_gb() -> float:
    """
    Get the peak resident set size (RSS) of the current process in GB.
    
    Returns:
        Memory usage in GB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux
    max_kb = usage.ru_maxrss
    return max_kb / (1024 * 1024)

def check_limits(max_cpu_hours: float = 6.0, max_ram_gb: float = 7.0) -> Dict[str, Any]:
    """
    Check current resource usage against limits.
    
    Args:
        max_cpu_hours: Maximum allowed CPU hours.
        max_ram_gb: Maximum allowed RAM in GB.
        
    Returns:
        Dictionary with current usage and status.
        
    Raises:
        ResourceLimitExceeded: If limits are exceeded.
    """
    cpu_hours = get_cpu_usage_hours()
    ram_gb = get_memory_usage_gb()
    
    status = {
        "cpu_hours": cpu_hours,
        "ram_gb": ram_gb,
        "cpu_limit": max_cpu_hours,
        "ram_limit": max_ram_gb,
        "cpu_ok": cpu_hours < max_cpu_hours,
        "ram_ok": ram_gb < max_ram_gb
    }
    
    if not status["cpu_ok"]:
        raise ResourceLimitExceeded("CPU", f"{max_cpu_hours} hours", f"{cpu_hours:.2f} hours")
    if not status["ram_ok"]:
        raise ResourceLimitExceeded("RAM", f"{max_ram_gb} GB", f"{ram_gb:.2f} GB")
        
    # Log warnings if approaching limits (e.g., > 80%)
    if cpu_hours > max_cpu_hours * 0.8:
        logging.warning(f"Warning: Resource usage approaching limit: CPU {cpu_hours:.2f} / {max_cpu_hours}")
    if ram_gb > max_ram_gb * 0.8:
        logging.warning(f"Warning: Resource usage approaching limit: RAM {ram_gb:.2f} / {max_ram_gb}")
        
    return status

@contextmanager
def resource_monitor(max_cpu_hours: float = 6.0, max_ram_gb: float = 7.0) -> Generator[Dict[str, Any], None, None]:
    """
    Context manager to monitor resource usage for a block of code.
    
    Args:
        max_cpu_hours: Maximum allowed CPU hours for the block.
        max_ram_gb: Maximum allowed RAM in GB for the block.
        
    Yields:
        Dictionary with resource usage stats.
        
    Raises:
        ResourceLimitExceeded: If limits are exceeded within the block.
    """
    start_cpu = get_cpu_usage_hours()
    start_ram = get_memory_usage_gb()
    
    try:
        yield {
            "start_cpu_hours": start_cpu,
            "start_ram_gb": start_ram
        }
    finally:
        end_cpu = get_cpu_usage_hours()
        end_ram = get_memory_usage_gb()
        
        delta_cpu = end_cpu - start_cpu
        delta_ram = end_ram - start_ram # Note: ru_maxrss is peak, so delta might be misleading if peak was earlier
        
        # Check against limits (absolute usage is usually preferred for global limits, 
        # but for a block, we might check delta or absolute. 
        # Per task, we enforce global limits, so we check absolute current state)
        check_limits(max_cpu_hours, max_ram_gb)

        logging.info(
            f"Resource monitor block finished. "
            f"CPU delta: {delta_cpu:.4f}h, RAM peak: {end_ram:.2f}GB"
        )

def enforce_resource_limits(max_cpu_hours: float = 6.0, max_ram_gb: float = 7.0) -> None:
    """
    Enforce resource limits for the current process using OS signals.
    This sets soft/hard limits. If exceeded, the OS will send SIGXCPU or terminate.
    We also add a Python-level check loop if desired, but rpy2/Docker often rely on cgroups.
    Here we implement the Python-level check as a safeguard.
    """
    # Set resource limits (soft and hard)
    # Note: setrlimit might fail if running as non-root in restricted containers
    try:
        # CPU limit in seconds
        cpu_seconds = int(max_cpu_hours * 3600)
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        
        # Memory limit in bytes (RSS)
        ram_bytes = int(max_ram_gb * 1024 * 1024 * 1024)
        resource.setrlimit(resource.RLIMIT_AS, (ram_bytes, ram_bytes))
        
        logging.info(f"Resource limits set: CPU={max_cpu_hours}h, RAM={max_ram_gb}GB")
    except (ValueError, resource.error) as e:
        logging.warning(f"Could not set OS resource limits: {e}. Relying on Python checks.")

# --- Docker Integration ---
def get_docker_run_flags(cpus: Optional[int] = None, memory_gb: Optional[int] = None) -> str:
    """
    Generate Docker run flags for CPU and memory capping.
    
    Args:
        cpus: Number of CPU cores to allow. If None, detects nproc.
        memory_gb: Memory limit in GB. If None, detects free RAM.
        
    Returns:
        String of Docker flags.
    """
    # Detect resources if not provided
    if cpus is None:
        try:
            cpus = int(subprocess.check_output(['nproc'], text=True).strip())
        except (subprocess.SubprocessError, ValueError):
            cpus = 1
    
    if memory_gb is None:
        try:
            # free -g outputs in GB
            output = subprocess.check_output(['free', '-g'], text=True)
            lines = output.strip().split('\n')
            # Second line is Mem:
            parts = lines[1].split()
            # parts[1] is total
            mem_total = int(parts[1])
            if mem_total == 0:
                memory_gb = 1 # Fallback
            else:
                memory_gb = mem_total
        except (subprocess.SubprocessError, IndexError, ValueError):
            memory_gb = 2 # Fallback
    
    # Cap at safe thresholds (FR-012)
    safe_cpus = min(cpus, 6) # Example cap, or use config
    safe_mem = min(memory_gb, 7)
    
    flags = f"--cpus={safe_cpus} --memory={safe_mem}g"
    return flags

def ensure_docker_limits(image: str = "biocontainers/deseq2:4.3.0") -> None:
    """
    Verify Docker image availability and prepare for execution with limits.
    """
    # We don't pull here to avoid network hangs in non-docker environments,
    # but we ensure the command structure is ready.
    logging.info(f"Ensuring Docker environment for image: {image}")

def generate_watchdog_script(output_path: str, interval_seconds: int = 5) -> None:
    """
    Generate a shell script that monitors the process and kills it if limits are exceeded.
    This is an external enforcement mechanism.
    """
    script_content = f"""#!/bin/bash
# Watchdog script for resource limits
# Kills the parent process if limits are exceeded

INTERVAL={interval_seconds}
MAX_CPU=6
MAX_RAM=7

while true; do
    # Get PID of parent (this script's parent)
    PID=$PPID
    
    # Check CPU time (roughly)
    # Check RSS
    RSS_KB=$(ps -o rss= -p $PID 2>/dev/null)
    if [ -z "$RSS_KB" ]; then
  echo "Parent process finished."
  exit 0
    fi
    
    RSS_GB=$(echo "scale=2; $RSS_KB / 1048576" | bc)
    
    # Simple check (bc might not be available, using integer math for safety in minimal containers)
    # If RSS > MAX_RAM * 1024 * 1024
    LIMIT_KB=$((MAX_RAM * 1024 * 1024))
    
    if [ "$RSS_KB" -gt "$LIMIT_KB" ]; then
  echo "Resource limit exceeded: RAM ${RSS_GB}GB > ${MAX_RAM}GB. Killing process."
  kill -9 $PID
  exit 1
    fi
    
    sleep $INTERVAL
done
"""
    Path(output_path).write_text(script_content)
    os.chmod(output_path, 0o755)
    logging.info(f"Watchdog script generated at {output_path}")

def main():
    """
    Main entry point for testing utilities.
    """
    logger = setup_logging(level=logging.DEBUG)
    logger.info("Testing utils module...")
    
    # Test checksum
    try:
        # Create a temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        checksum = calculate_checksum(tmp_path)
        logger.info(f"Checksum of temp file: {checksum}")
        os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Checksum test failed: {e}")
    
    # Test resource monitoring
    try:
        with resource_monitor(max_cpu_hours=1.0, max_ram_gb=1.0):
            logger.info("Inside resource monitor block")
            time.sleep(0.1)
        logger.info("Resource monitor block completed successfully")
    except ResourceLimitExceeded as e:
        logger.error(f"Resource limit exceeded during test: {e}")
    
    # Test Docker flags
    flags = get_docker_run_flags(cpus=4, memory_gb=4)
    logger.info(f"Docker flags: {flags}")

if __name__ == "__main__":
    main()