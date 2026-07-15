"""
Environment configuration management for CI limits (limited CPU, constrained RAM).

This module provides functions to detect, configure, and validate resource limits
for running the simulation pipeline in constrained CI environments.
"""
import os
import multiprocessing
import logging
import resource
from typing import Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# Default limits for CI environments
DEFAULT_MAX_CPU_PERCENT = 200  # 2 cores equivalent
DEFAULT_MAX_MEMORY_GB = 4.0    # 4 GB RAM limit
DEFAULT_PARALLELISM_FACTOR = 0.5  # Use 50% of available CPUs

def get_cpu_limit() -> int:
    """
    Determine the maximum number of CPU cores to use based on environment.
    
    Checks for CI environment variables (CI, GITHUB_ACTIONS, GITLAB_CI, etc.)
    and applies appropriate limits. Returns a safe integer count.
    
    Returns:
        int: Number of CPU cores to use
    """
    # Check for CI environment
    is_ci = (
        os.getenv('CI', '').lower() in ('true', '1', 'yes') or
        os.getenv('GITHUB_ACTIONS', '').lower() in ('true', '1', 'yes') or
        os.getenv('GITLAB_CI', '').lower() in ('true', '1', 'yes') or
        os.getenv('TRAVIS', '').lower() in ('true', '1', 'yes') or
        os.getenv('CIRCLECI', '').lower() in ('true', '1', 'yes')
    )
    
    # Check for explicit CPU limit configuration
    cpu_limit_env = os.getenv('MAX_CPU_CORES')
    if cpu_limit_env:
        try:
            return max(1, int(cpu_limit_env))
        except ValueError:
            logger.warning(f"Invalid MAX_CPU_CORES value: {cpu_limit_env}, using default")
    
    if is_ci:
        # In CI, use a conservative limit
        return 2
    
    # For local development, use half of available CPUs
    available_cpus = multiprocessing.cpu_count()
    return max(1, int(available_cpus * DEFAULT_PARALLELISM_FACTOR))

def get_memory_limit_gb() -> float:
    """
    Determine the maximum memory limit in GB.
    
    Checks for CI environment and explicit memory configuration.
    
    Returns:
        float: Memory limit in GB
    """
    # Check for CI environment
    is_ci = (
        os.getenv('CI', '').lower() in ('true', '1', 'yes') or
        os.getenv('GITHUB_ACTIONS', '').lower() in ('true', '1', 'yes') or
        os.getenv('GITLAB_CI', '').lower() in ('true', '1', 'yes') or
        os.getenv('TRAVIS', '').lower() in ('true', '1', 'yes') or
        os.getenv('CIRCLECI', '').lower() in ('true', '1', 'yes')
    )
    
    # Check for explicit memory limit configuration
    mem_limit_env = os.getenv('MAX_MEMORY_GB')
    if mem_limit_env:
        try:
            return float(mem_limit_env)
        except ValueError:
            logger.warning(f"Invalid MAX_MEMORY_GB value: {mem_limit_env}, using default")
    
    if is_ci:
        return DEFAULT_MAX_MEMORY_GB
    
    # For local development, use a more generous limit
    try:
        # Try to get total system memory
        total_mem = resource.getrlimit(resource.RLIMIT_AS)[0]
        if total_mem != resource.RLIM_INFINITY and total_mem > 0:
            return min(16.0, total_mem / (1024**3))
    except Exception:
        pass
    
    return 8.0  # Default for local development

def get_parallelism_config() -> Tuple[int, float]:
    """
    Get configuration for parallel processing.
    
    Returns:
        Tuple[int, float]: (max_workers, memory_per_worker_gb)
    """
    max_workers = get_cpu_limit()
    total_memory_gb = get_memory_limit_gb()
    
    # Ensure at least 1 worker and reasonable memory per worker
    if max_workers < 1:
        max_workers = 1
    
    memory_per_worker = total_memory_gb / max_workers
    
    # If memory per worker is too low, reduce parallelism
    MIN_MEMORY_PER_WORKER_GB = 0.5
    while memory_per_worker < MIN_MEMORY_PER_WORKER_GB and max_workers > 1:
        max_workers -= 1
        memory_per_worker = total_memory_gb / max_workers
    
    return max_workers, memory_per_worker

def validate_resources() -> bool:
    """
    Validate that the current environment has sufficient resources.
    
    Checks current memory usage against limits and logs warnings if
    approaching limits.
    
    Returns:
        bool: True if resources are sufficient, False otherwise
    """
    try:
        # Get current memory usage (RSS - Resident Set Size)
        current_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Convert to GB (on some systems ru_maxrss is in KB, on others in bytes)
        # Try to detect the unit
        if current_mem > 1024 * 1024:
            # Likely in bytes
            current_mem_gb = current_mem / (1024**3)
        else:
            # Likely in KB
            current_mem_gb = current_mem / (1024**2)
        
        limit_gb = get_memory_limit_gb()
        
        usage_percent = (current_mem_gb / limit_gb) * 100
        
        if usage_percent > 90:
            logger.error(f"Memory usage at {usage_percent:.1f}% of limit ({current_mem_gb:.2f}/{limit_gb:.2f} GB)")
            return False
        elif usage_percent > 75:
            logger.warning(f"Memory usage at {usage_percent:.1f}% of limit ({current_mem_gb:.2f}/{limit_gb:.2f} GB)")
        
        return True
    except Exception as e:
        logger.warning(f"Could not validate memory usage: {e}")
        return True  # Be permissive if we can't check

def configure_environment() -> None:
    """
    Configure the environment for constrained execution.
    
    Sets environment variables and applies resource limits for CI environments.
    This should be called at the start of the main execution.
    """
    # Set environment variables for other libraries
    os.environ['OMP_NUM_THREADS'] = str(get_cpu_limit())
    os.environ['MKL_NUM_THREADS'] = str(get_cpu_limit())
    os.environ['OPENBLAS_NUM_THREADS'] = str(get_cpu_limit())
    os.environ['VECLIB_MAXIMUM_THREADS'] = str(get_cpu_limit())
    os.environ['NUMEXPR_NUM_THREADS'] = str(get_cpu_limit())
    
    # Set memory limits for subprocesses
    limit_gb = get_memory_limit_gb()
    limit_bytes = int(limit_gb * 1024**3)
    
    try:
        # Apply soft and hard memory limits
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, hard_limit))
        logger.info(f"Set memory limit to {limit_gb:.2f} GB")
    except Exception as e:
        logger.warning(f"Could not set memory limit: {e}")
    
    # Configure logging for resource monitoring
    logger.info(f"Configured for {get_cpu_limit()} CPU cores and {limit_gb:.2f} GB memory")
    logger.info(f"Parallelism config: {get_parallelism_config()}")
    
    # Validate resources
    if not validate_resources():
        logger.error("Insufficient resources for safe execution")
        raise MemoryError("Insufficient memory for execution")
    
    logger.info("Environment configuration completed successfully")

def get_resource_monitor() -> dict:
    """
    Get current resource usage statistics.
    
    Returns:
        dict: Current resource usage information
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return {
            'user_time': usage.ru_utime,
            'system_time': usage.ru_stime,
            'max_rss_kb': usage.ru_maxrss,
            'max_rss_gb': usage.ru_maxrss / (1024**2) if usage.ru_maxrss > 1024*1024 else usage.ru_maxrss / 1024,
            'cpu_limit': get_cpu_limit(),
            'memory_limit_gb': get_memory_limit_gb(),
        }
    except Exception as e:
        logger.error(f"Could not get resource usage: {e}")
        return {}