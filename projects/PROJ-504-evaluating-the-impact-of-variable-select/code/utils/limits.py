"""
Resource limits and environment configuration for CI/CD constraints.

Explicitly manages vCPU and RAM constraints to ensure the pipeline
respects the system limits defined in FR-008, SC-003, and SC-004.
"""
import os
import multiprocessing
import logging
import resource
from typing import Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Default constraints based on CI environment specifications (2 vCPU, 7GB RAM)
# These can be overridden via environment variables:
#   MAX_VCPU: Maximum number of CPU cores allowed
#   MAX_RAM_GB: Maximum RAM in Gigabytes allowed
DEFAULT_MAX_VCPU = 2
DEFAULT_MAX_RAM_GB = 7.0

def get_cpu_limit() -> int:
    """
    Determine the maximum number of CPU cores to use.
    
    Checks environment variable MAX_VCPU first, then falls back to
    detecting available CPUs and capping at DEFAULT_MAX_VCPU.
    
    Returns:
        int: The number of CPU cores to use.
    """
    env_cpu = os.getenv("MAX_VCPU")
    if env_cpu:
        try:
            return int(env_cpu)
        except ValueError:
            logger.warning(f"Invalid MAX_VCPU value '{env_cpu}', using default.")
    
    # Detect available CPUs but cap at default
    available = multiprocessing.cpu_count()
    limit = min(available, DEFAULT_MAX_VCPU)
    
    logger.info(f"CPU limit set to {limit} (detected: {available}, max allowed: {DEFAULT_MAX_VCPU})")
    return limit

def get_memory_limit_gb() -> float:
    """
    Determine the maximum RAM limit in Gigabytes.
    
    Checks environment variable MAX_RAM_GB first, then falls back to
    detecting available memory and capping at DEFAULT_MAX_RAM_GB.
    
    Returns:
        float: The memory limit in GB.
    """
    env_ram = os.getenv("MAX_RAM_GB")
    if env_ram:
        try:
            return float(env_ram)
        except ValueError:
            logger.warning(f"Invalid MAX_RAM_GB value '{env_ram}', using default.")
    
    # Try to detect physical memory (Linux/Mac/Windows)
    try:
        # Linux: /proc/meminfo
        if os.path.exists('/proc/meminfo'):
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        # Value is in kB
                        mem_kb = int(line.split()[1])
                        mem_gb = mem_kb / (1024 ** 2)
                        limit = min(mem_gb, DEFAULT_MAX_RAM_GB)
                        logger.info(f"RAM limit set to {limit:.2f} GB (detected: {mem_gb:.2f} GB, max allowed: {DEFAULT_MAX_RAM_GB})")
                        return limit
        
        # Fallback for other OS or if /proc not available
        # Use resource module if available (Unix)
        if hasattr(resource, 'getrlimit'):
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            if soft != resource.RLIM_INFINITY:
                mem_gb = soft / (1024 ** 3)
                limit = min(mem_gb, DEFAULT_MAX_RAM_GB)
                logger.info(f"RAM limit set to {limit:.2f} GB (from RLIMIT_AS, max allowed: {DEFAULT_MAX_RAM_GB})")
                return limit
    except Exception as e:
        logger.warning(f"Could not detect physical memory: {e}")
    
    # Final fallback
    logger.warning(f"Could not detect memory, using default limit of {DEFAULT_MAX_RAM_GB} GB")
    return DEFAULT_MAX_RAM_GB

def get_parallelism_config() -> Tuple[int, float]:
    """
    Get the parallelism configuration (CPU count, memory limit).
    
    Returns:
        Tuple[int, float]: (max_workers, max_memory_gb)
    """
    cpu_limit = get_cpu_limit()
    mem_limit = get_memory_limit_gb()
    return cpu_limit, mem_limit

def validate_resources() -> bool:
    """
    Validate that the current environment meets the minimum requirements.
    
    Returns:
        bool: True if resources are sufficient, False otherwise.
    """
    cpu_limit = get_cpu_limit()
    mem_limit = get_memory_limit_gb()
    
    if cpu_limit < 1:
        logger.error("Insufficient CPU resources: need at least 1 core")
        return False
    
    if mem_limit < 2.0:
        logger.error(f"Insufficient RAM resources: need at least 2 GB, got {mem_limit:.2f} GB")
        return False
    
    logger.info(f"Resource validation passed: {cpu_limit} vCPU, {mem_limit:.2f} GB RAM")
    return True

def configure_environment() -> None:
    """
    Configure the environment to respect resource limits.
    
    Sets environment variables and logging to ensure downstream tasks
    are aware of the constraints.
    """
    cpu_limit = get_cpu_limit()
    mem_limit = get_memory_limit_gb()
    
    os.environ["MAX_VCPU"] = str(cpu_limit)
    os.environ["MAX_RAM_GB"] = str(mem_limit)
    
    logger.info(f"Environment configured: vCPU={cpu_limit}, RAM={mem_limit:.2f} GB")

def get_resource_monitor() -> dict:
    """
    Get current resource usage statistics.
    
    Returns:
        dict: Current CPU and memory usage statistics.
    """
    try:
        # Get current process memory usage
        if hasattr(resource, 'getrusage'):
            usage = resource.getrusage(resource.RUSAGE_SELF)
            max_rss_mb = usage.ru_maxrss / 1024  # Convert KB to MB (Linux)
        else:
            max_rss_mb = 0.0
        
        return {
            "cpu_count": multiprocessing.cpu_count(),
            "cpu_limit": get_cpu_limit(),
            "memory_limit_gb": get_memory_limit_gb(),
            "current_memory_mb": max_rss_mb
        }
    except Exception as e:
        logger.warning(f"Could not get resource usage: {e}")
        return {
            "cpu_count": multiprocessing.cpu_count(),
            "cpu_limit": get_cpu_limit(),
            "memory_limit_gb": get_memory_limit_gb(),
            "current_memory_mb": 0.0
        }
