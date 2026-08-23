import hashlib
import json
import logging
import os
import resource
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# --- Resource Monitoring ---

class ResourceLimitExceeded(Exception):
    """Raised when resource limits (CPU/Memory) are exceeded."""
    pass

class ResourceWarning(Exception):
    """Raised when resource usage is approaching limits."""
    pass

def detect_resources() -> Tuple[int, float]:
    """Detect available CPU cores and memory limit (GB)."""
    try:
        cpu_count = os.cpu_count() or 1
        # Try to get memory limit from cgroup if available, else fallback to system
        mem_limit_bytes = None
        cgroup_mem_path = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
        if os.path.exists(cgroup_mem_path):
            with open(cgroup_mem_path, "r") as f:
                limit_str = f.read().strip()
                if limit_str != "max" and limit_str != "9223372036854775807":
                    mem_limit_bytes = int(limit_str)
        else:
            # Fallback to resource.getrlimit
            soft, _ = resource.getrlimit(resource.RLIMIT_AS)
            if soft != resource.RLIM_INFINITY:
                mem_limit_bytes = soft

        if mem_limit_bytes:
            mem_limit_gb = mem_limit_bytes / (1024 ** 3)
        else:
            # Fallback to total system memory if cgroup not found
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            mem_total_kb = int(line.split()[1])
                            mem_limit_gb = mem_total_kb / (1024 * 1024)
                            break
                    else:
                        mem_limit_gb = 16.0 # Default fallback
            except FileNotFoundError:
                mem_limit_gb = 16.0 # Default fallback

        return cpu_count, mem_limit_gb
    except Exception as e:
        logging.warning(f"Failed to detect resources: {e}. Using defaults.")
        return 4, 8.0

def calculate_caps(cpu_count: int, mem_limit_gb: float) -> Dict[str, Any]:
    """Calculate safe operational caps based on detected resources."""
    # Heuristic: 1 thread per 2GB RAM, max 8 threads
    max_threads = min(cpu_count, int(mem_limit_gb / 2))
    max_threads = max(1, min(max_threads, 8))

    # Heuristic: 70% of memory for data, rest for overhead
    safe_memory_gb = mem_limit_gb * 0.7

    return {
        "max_threads": max_threads,
        "safe_memory_gb": safe_memory_gb,
        "chunk_size_mb": int(safe_memory_gb * 1024 * 0.1) # 10% of safe mem per chunk
    }

def get_cpu_usage_hours() -> float:
    """Get CPU time used in hours (user + system)."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    total_seconds = usage.ru_utime + usage.ru_stime
    return total_seconds / 3600.0

def get_memory_usage_gb() -> float:
    """Get peak memory usage in GB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux
    return usage.ru_maxrss / (1024 * 1024)

def check_limits(cpu_count: int, mem_limit_gb: float, caps: Dict[str, Any]) -> bool:
    """Check if current usage exceeds limits."""
    current_mem = get_memory_usage_gb()
    if current_mem > caps["safe_memory_gb"]:
        logging.error(f"Memory limit exceeded: {current_mem:.2f}GB > {caps['safe_memory_gb']:.2f}GB")
        return False
    return True

def resource_monitor(cpu_count: int, mem_limit_gb: float, caps: Dict[str, Any]) -> None:
    """Periodic monitor (simplified for single script execution)."""
    if not check_limits(cpu_count, mem_limit_gb, caps):
        raise ResourceLimitExceeded("Resource limits exceeded during execution.")

def enforce_resource_limits(cpu_count: int, mem_limit_gb: float) -> None:
    """Attempt to set soft limits (best effort)."""
    try:
        # Set soft limit to 80% of hard limit (or detected limit)
        soft_limit = int(mem_limit_gb * 0.8 * 1024 * 1024 * 1024)
        hard_limit = int(mem_limit_gb * 1024 * 1024 * 1024)
        resource.setrlimit(resource.RLIMIT_AS, (soft_limit, hard_limit))
    except (ValueError, resource.error) as e:
        logging.warning(f"Could not enforce resource limits: {e}")

# --- Data Integrity & Checksums ---

def calculate_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.
    
    CRITICAL: This function strictly enforces data integrity.
    It does NOT generate synthetic data or fallback to mock values.
    If the file does not exist or cannot be read, it raises FileNotFoundError.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).
    
    Returns:
        Hex digest string.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
        ValueError: If the file is empty (indicating a potential download failure).
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Data integrity check failed: File not found at {file_path}")
    
    if path.stat().st_size == 0:
        raise ValueError(f"Data integrity check failed: File is empty at {file_path}. Download may have failed.")

    hash_func = hashlib.new(algorithm)
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
    except PermissionError as e:
        raise PermissionError(f"Data integrity check failed: Cannot read file {file_path}") from e
    
    return hash_func.hexdigest()

def get_docker_run_flags() -> List[str]:
    """Get standard Docker run flags for the pipeline."""
    # Default flags for the R/Python environment
    return [
        "--rm",
        "-v", f"{Path.cwd()}:/work",
        "-w", "/work",
        "-e", "PYTHONUNBUFFERED=1"
    ]

def ensure_docker_limits(cpu_count: int, mem_limit_gb: float) -> List[str]:
    """Generate Docker flags to enforce resource limits."""
    return [
        "--cpus", str(cpu_count),
        "--memory", f"{int(mem_limit_gb)}g",
        "--memory-swap", f"{int(mem_limit_gb)}g"
    ]

def generate_watchdog_script(output_path: str) -> None:
    """Generate a simple bash watchdog script (optional utility)."""
    script_content = """#!/bin/bash
    # Watchdog script to monitor process memory
    PID=$1
    LIMIT_GB=$2
    while kill -0 $PID 2>/dev/null; do
        MEM_KB=$(ps -o rss= -p $PID 2>/dev/null)
        if [ -n "$MEM_KB" ]; then
            MEM_GB=$(echo "$MEM_KB / 1024 / 1024" | bc)
            if (( $(echo "$MEM_GB > $LIMIT_GB" | bc -l) )); then
                echo "Memory limit exceeded. Killing process $PID."
                kill -9 $PID
                exit 1
            fi
        fi
        sleep 10
    done
    """
    with open(output_path, "w") as f:
        f.write(script_content)
    os.chmod(output_path, 0o755)

# --- Logging Setup ---

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the pipeline."""
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    
    return logger

def main():
    """Main entry point for utility tests/demo (not used in pipeline)."""
    pass
