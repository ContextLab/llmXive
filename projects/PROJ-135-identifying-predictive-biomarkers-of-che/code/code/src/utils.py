import hashlib
import json
import logging
import os
import resource
import signal
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import psutil
import multiprocessing

class ResourceWarning(Warning):
    """Warning raised when resource usage approaches limits."""
    pass

class ResourceLimitExceeded(RuntimeError):
    """Exception raised when resource limits are exceeded."""
    pass

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("project")
    logger.setLevel(log_level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def detect_resources() -> Dict[str, Any]:
    """
    Detect available CPU cores and RAM (GB).
    Checks Docker environment variables and /proc/cgroup first.
    Falls back to system defaults.
    """
    logger = logging.getLogger("project")
    
    # Detect Docker environment
    in_docker = False
    if os.path.exists('/proc/1/cgroup'):
        with open('/proc/1/cgroup', 'r') as f:
            content = f.read()
            if 'docker' in content or 'kubepods' in content:
                in_docker = True
    
    # Check environment variables for Docker constraints
    docker_cpus = os.environ.get('DOCKER_CPUS')
    docker_memory = os.environ.get('DOCKER_MEMORY')
    
    if docker_cpus:
        try:
            detected_cpus = int(docker_cpus)
        except ValueError:
            detected_cpus = multiprocessing.cpu_count()
    else:
        detected_cpus = multiprocessing.cpu_count()
    
    if docker_memory:
        try:
            detected_ram_gb = float(docker_memory)
        except ValueError:
            detected_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    else:
        detected_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    
    logger.info(f"Detected resources: {detected_cpus} CPUs, {detected_ram_gb:.2f} GB RAM")
    return {
        'cpus': detected_cpus,
        'ram_gb': detected_ram_gb,
        'time_limit_hours': 24
    }

def calculate_caps(resources: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate capped values based on safe thresholds mandated by FR-012, SC-004, SC-005.
    """
    # Safe thresholds
    MAX_CPUS = 8
    MAX_RAM_GB = 16.0
    MAX_TIME_HOURS = 12
    
    capped = {
        'cpus': min(resources['cpus'], MAX_CPUS),
        'ram_gb': min(resources['ram_gb'], MAX_RAM_GB),
        'time_limit_hours': min(resources['time_limit_hours'], MAX_TIME_HOURS)
    }
    
    return capped

def check_limits(current_usage: Dict[str, Any], caps: Dict[str, Any]) -> bool:
    """
    Check if current usage exceeds substantial majority of caps.
    Returns True if limits are breached.
    """
    threshold = 0.90  # 90% threshold
    
    if current_usage['cpus'] > caps['cpus'] * threshold:
        logging.warning(f"Warning: Resource usage approaching limit: CPUs {current_usage['cpus']} / {caps['cpus']}")
        return True
    
    if current_usage['ram_gb'] > caps['ram_gb'] * threshold:
        logging.warning(f"Warning: Resource usage approaching limit: RAM {current_usage['ram_gb']} / {caps['ram_gb']} GB")
        return True
        
    return False

def get_cpu_usage_hours() -> float:
    """Get current CPU time usage in hours."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return (usage.ru_utime + usage.ru_stime) / 3600.0

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / (1024 * 1024)  # Convert KB to GB

def resource_monitor(caps: Dict[str, Any]):
    """Monitor resource usage and raise warnings."""
    current = {
        'cpus': multiprocessing.cpu_count(),
        'ram_gb': get_memory_usage_gb()
    }
    if check_limits(current, caps):
        logging.warning("Warning: Resource usage approaching limit. Consider optimizing.")

def enforce_resource_limits(caps: Dict[str, Any]):
    """Enforce resource limits by setting soft/hard limits."""
    # Set memory limit (in bytes)
    ram_bytes = int(caps['ram_gb'] * 1024 * 1024 * 1024)
    resource.setrlimit(resource.RLIMIT_AS, (ram_bytes, ram_bytes))
    logging.info(f"Enforced memory limit: {caps['ram_gb']} GB")

def build_docker_run_cmd(image: str, volume: str, cpus: int, memory: float) -> str:
    """
    Construct the docker run command with resource limits.
    """
    cmd = f"docker run --rm --cpus={cpus} --memory={memory}g -v {volume}:{volume} {image}"
    return cmd

def run_docker_with_enforcement(image: str, volume: str, cpus: int, memory: float):
    """
    Execute docker run command with enforcement and error handling.
    """
    cmd = build_docker_run_cmd(image, volume, cpus, memory)
    logging.info(f"Running command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        if e.returncode == 137:
            raise ResourceLimitExceeded(f"Resource limit exceeded (Exit Code 137): System enforced termination per FR-012. Check logs for details.")
        elif e.returncode == 124:
            raise ResourceLimitExceeded(f"Resource limit exceeded (Exit Code 124): System enforced termination per FR-012. Check logs for details.")
        else:
            raise

def calculate_checksum(file_path: str) -> str:
    """
    Compute SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_docker_limits(caps: Dict[str, Any]):
    """Ensure Docker limits are set correctly."""
    if os.environ.get('DOCKER_CPUS') is None:
        os.environ['DOCKER_CPUS'] = str(caps['cpus'])
    if os.environ.get('DOCKER_MEMORY') is None:
        os.environ['DOCKER_MEMORY'] = str(caps['ram_gb'])
    logging.info(f"Docker limits set: CPUs={caps['cpus']}, RAM={caps['ram_gb']}GB")

def main():
    """Main entry point for utility functions."""
    logging.basicConfig(level=logging.INFO)
    resources = detect_resources()
    caps = calculate_caps(resources)
    logging.info(f"Resource caps: {caps}")
    ensure_docker_limits(caps)

if __name__ == "__main__":
    main()
