import hashlib
import json
import logging
import os
import resource
import signal
import subprocess
import sys
import multiprocessing
from pathlib import Path
from typing import Dict, Any, Optional
import psutil

# Custom Exceptions and Warnings
class ResourceWarning(Warning):
    """Warning for approaching resource limits."""
    pass

class ResourceLimitExceeded(RuntimeError):
    """Raised when a resource limit is strictly exceeded."""
    pass

# Logging Setup
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level.upper()))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logging()

# Resource Detection Logic
def detect_resources() -> Dict[str, Any]:
    """
    Detect available CPU cores and RAM (GB) inside a Docker container.
    If not in Docker, fallback to system defaults.
    Returns dict: {'cpus': int, 'ram_gb': float, 'time_limit_hours': int}
    """
    cpus = None
    ram_bytes = None

    # 1. Check Docker Environment Variables first
    docker_cpus = os.environ.get("DOCKER_CPUS")
    docker_memory = os.environ.get("DOCKER_MEMORY")

    if docker_cpus:
        try:
            cpus = int(docker_cpus)
        except ValueError:
            logger.warning(f"Invalid DOCKER_CPUS value: {docker_cpus}, falling back.")

    if docker_memory:
        try:
            # Memory often in MB or bytes, assume MB if small, bytes if large
            mem_val = float(docker_memory)
            if mem_val < 10000:
                ram_bytes = int(mem_val * 1024 * 1024) # MB to Bytes
            else:
                ram_bytes = int(mem_val) # Assume bytes
        except ValueError:
            logger.warning(f"Invalid DOCKER_MEMORY value: {docker_memory}, falling back.")

    # 2. Check /proc/cgroup for cgroup constraints (Docker)
    if cpus is None:
        try:
            with open("/proc/cpuinfo", "r") as f:
                # Count cores based on cgroup quota if available, else physical
                # Simplified: check if running in container via cgroup
                cgroup_path = "/proc/self/cgroup"
                if os.path.exists(cgroup_path):
                    with open(cgroup_path, "r") as cg:
                        content = cg.read()
                        if "docker" in content or "kubepods" in content:
                            # Try to read CPU quota
                            cpu_quota_path = "/sys/fs/cgroup/cpu/cpu.cfs_quota_us"
                            cpu_period_path = "/sys/fs/cgroup/cpu/cpu.cfs_period_us"
                            if os.path.exists(cpu_quota_path) and os.path.exists(cpu_period_path):
                                with open(cpu_quota_path, "r") as q:
                                    quota = int(q.read().strip())
                                with open(cpu_period_path, "r") as p:
                                    period = int(p.read().strip())
                                if period > 0 and quota > 0:
                                    cpus = max(1, int(quota / period))
                                else:
                                    cpus = multiprocessing.cpu_count()
                            else:
                                cpus = multiprocessing.cpu_count()
                        else:
                            cpus = multiprocessing.cpu_count()
                else:
                    cpus = multiprocessing.cpu_count()
        except Exception as e:
            logger.warning(f"Could not read /proc/cgroup: {e}. Using system default.")
            cpus = multiprocessing.cpu_count()

    if ram_bytes is None:
        try:
            # Check cgroup memory limit
            mem_limit_path = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
            if os.path.exists(mem_limit_path):
                with open(mem_limit_path, "r") as f:
                    val = int(f.read().strip())
                    # 9223372036854771712 is often the default "unlimited"
                    if val < 9223372036854771712:
                        ram_bytes = val
                    else:
                        ram_bytes = psutil.virtual_memory().total
            else:
                ram_bytes = psutil.virtual_memory().total
        except Exception as e:
            logger.warning(f"Could not read memory limit: {e}. Using system total.")
            ram_bytes = psutil.virtual_memory().total

    ram_gb = ram_bytes / (1024 ** 3)
    # Default time limit based on constraints (e.g., 24 hours)
    time_limit_hours = 24

    # Log detected resources
    logger.info(f"Detected Resources: CPUs={cpus}, RAM={ram_gb:.2f} GB")

    return {
        'cpus': cpus,
        'ram_gb': ram_gb,
        'time_limit_hours': time_limit_hours
    }

def calculate_caps(detected: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate capped values as the minimum of detected resources and safe thresholds.
    Thresholds defined by FR-012, SC-004, SC-005.
    """
    MAX_CPUS = 8 # Hard cap for safety
    MAX_RAM_GB = 16.0 # Hard cap for safety
    MAX_TIME_HOURS = 48 # Hard cap for safety

    caps = {
        'cpus': min(detected['cpus'], MAX_CPUS),
        'ram_gb': min(detected['ram_gb'], MAX_RAM_GB),
        'time_limit_hours': min(detected['time_limit_hours'], MAX_TIME_HOURS)
    }
    return caps

def check_limits(current_usage: Dict[str, float], caps: Dict[str, float], threshold: float = 0.9) -> bool:
    """
    Check if current usage exceeds a substantial majority threshold of the caps.
    Returns True if limit is exceeded (warning should be raised).
    """
    for key in ['cpus', 'ram_gb']:
        if key in caps and key in current_usage:
            if current_usage[key] > caps[key] * threshold:
                msg = f"Warning: Resource usage approaching limit: {key} {current_usage[key]:.2f} / {caps[key]:.2f}. Per FR-012, SC-004, SC-005."
                logger.warning(msg)
                return True
    return False

def get_cpu_usage_hours() -> float:
    # Placeholder for actual CPU time tracking if needed
    return 0.0

def get_memory_usage_gb() -> float:
    usage = psutil.Process().memory_info().rss
    return usage / (1024 ** 3)

def resource_monitor(caps: Dict[str, Any], interval: float = 5.0) -> None:
    """
    Monitor resource usage periodically.
    """
    # Implementation would involve a loop or signal handler
    # For now, a simple check
    current = {
        'cpus': psutil.cpu_percent(interval=1) / 100.0 * caps['cpus'], # Approximation
        'ram_gb': get_memory_usage_gb()
    }
    check_limits(current, caps)

def enforce_resource_limits(caps: Dict[str, Any]) -> None:
    """
    Enforce resource limits using signal handlers or resource module.
    """
    # Set memory limit
    try:
        # Convert GB to bytes for resource module (soft/hard)
        limit_bytes = int(caps['ram_gb'] * 1024 * 1024 * 1024)
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
    except (ValueError, resource.error) as e:
        logger.warning(f"Could not set memory limit: {e}")

def build_docker_run_cmd(image: str, volume: str, cpus: Optional[int] = None, memory: Optional[float] = None) -> str:
    """
    Construct the docker run command with --cpus and --memory flags.
    """
    if cpus is None or memory is None:
        detected = detect_resources()
        caps = calculate_caps(detected)
        cpus = cpus or caps['cpus']
        memory = memory or caps['ram_gb']

    cmd = f"docker run --rm --cpus={cpus} --memory={memory:g}g -v {volume}:/work {image}"
    return cmd

def run_docker_with_enforcement(cmd: str) -> subprocess.CompletedProcess:
    """
    Execute the docker command and handle specific exit codes.
    """
    try:
        result = subprocess.run(cmd, shell=True, check=False)
        if result.returncode == 137:
            raise ResourceLimitExceeded("Resource limit exceeded (Exit Code 137): System enforced termination per FR-012. Check logs for details.")
        elif result.returncode == 124:
            raise ResourceLimitExceeded("Resource limit exceeded (Exit Code 124): Timeout enforced per FR-012. Check logs for details.")
        elif result.returncode != 0:
            raise RuntimeError(f"Docker command failed with exit code {result.returncode}")
        return result
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Failed to execute docker command: {e}")

def calculate_checksum(file_path: str) -> str:
    """
    Compute SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_docker_limits() -> None:
    """
    Ensure Docker limits are respected if running in Docker.
    """
    if os.path.exists("/.dockerenv"):
        detected = detect_resources()
        caps = calculate_caps(detected)
        enforce_resource_limits(caps)

def main():
    """Main entry point for utils testing/demo."""
    detected = detect_resources()
    caps = calculate_caps(detected)
    print(f"Detected: {detected}")
    print(f"Capped: {caps}")

if __name__ == "__main__":
    main()
