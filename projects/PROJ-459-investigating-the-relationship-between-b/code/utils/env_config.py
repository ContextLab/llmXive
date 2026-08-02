import os
import sys
import resource
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Default limits if environment variables are not set
DEFAULT_MEMORY_LIMIT_GB = 14.0
DEFAULT_RUNTIME_CAP_SECONDS = 3600  # 1 hour

def get_available_memory_gb() -> float:
    """
    Detects the available physical memory on the system.
    Uses /proc/meminfo on Linux or resource limits on other systems.
    Returns the value in Gigabytes.
    """
    if sys.platform.startswith('linux'):
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemAvailable:'):
                        # Value is in kB
                        mem_kb = int(line.split()[1])
                        return mem_kb / (1024.0 * 1024.0)
            # Fallback to MemTotal if Available is not found
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        mem_kb = int(line.split()[1])
                        return mem_kb / (1024.0 * 1024.0)
        except Exception as e:
            logger.warning(f"Could not read /proc/meminfo: {e}. Using default limit.")
            return DEFAULT_MEMORY_LIMIT_GB
    else:
        # Fallback for macOS/Windows or if /proc fails
        # resource.getrlimit(resource.RLIMIT_AS) might be -1 (unlimited)
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            if hard != resource.RLIM_INFINITY and hard != -1:
                return hard / (1024.0 * 1024.0 * 1024.0)
        except Exception:
            pass
        return DEFAULT_MEMORY_LIMIT_GB

def check_memory_limit(limit_gb: Optional[float] = None) -> Tuple[bool, float]:
    """
    Checks if the current environment has enough available memory.
    
    Args:
        limit_gb: The required memory limit in GB. If None, uses the 
                  default or environment variable LLMXIVE_MEMORY_LIMIT_GB.
    
    Returns:
        Tuple[bool, float]: (is_valid, available_gb)
        - is_valid: True if available memory >= limit_gb
        - available_gb: The detected available memory in GB
    
    Raises:
        RuntimeError: If memory is insufficient and the system is configured to fail.
    """
    available = get_available_memory_gb()
    
    # Determine limit: Env var > Argument > Default
    env_limit = os.getenv('LLMXIVE_MEMORY_LIMIT_GB')
    if limit_gb is None:
        if env_limit:
            try:
                limit_gb = float(env_limit)
            except ValueError:
                logger.warning(f"Invalid LLMXIVE_MEMORY_LIMIT_GB value: {env_limit}. Using default.")
                limit_gb = DEFAULT_MEMORY_LIMIT_GB
        else:
            limit_gb = DEFAULT_MEMORY_LIMIT_GB

    is_valid = available >= limit_gb
    
    if not is_valid:
        msg = f"Memory limit check failed: Available {available:.2f}GB < Required {limit_gb:.2f}GB"
        logger.error(msg)
        # Fail loudly as per constraints
        raise RuntimeError(msg)
    
    logger.info(f"Memory check passed: {available:.2f}GB available >= {limit_gb:.2f}GB limit.")
    return is_valid, available

def set_runtime_cap(seconds: Optional[int] = None) -> int:
    """
    Sets the maximum runtime for the current process using resource limits.
    
    Args:
        seconds: The maximum runtime in seconds. If None, uses the 
                 default or environment variable LLMXIVE_RUNTIME_CAP_SECONDS.
    
    Returns:
        int: The effective runtime cap in seconds.
    
    Raises:
        RuntimeError: If the limit cannot be set.
    """
    # Determine cap: Env var > Argument > Default
    env_cap = os.getenv('LLMXIVE_RUNTIME_CAP_SECONDS')
    if seconds is None:
        if env_cap:
            try:
                seconds = int(env_cap)
            except ValueError:
                logger.warning(f"Invalid LLMXIVE_RUNTIME_CAP_SECONDS value: {env_cap}. Using default.")
                seconds = DEFAULT_RUNTIME_CAP_SECONDS
        else:
            seconds = DEFAULT_RUNTIME_CAP_SECONDS

    try:
        # Set soft and hard limits
        resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
        logger.info(f"Runtime cap set to {seconds} seconds.")
    except ValueError as e:
        # This can happen on some systems (e.g., Windows) where RLIMIT_CPU is not supported
        logger.warning(f"Could not set RLIMIT_CPU (not supported on this OS?): {e}. Running without cap.")
        return 0
    except Exception as e:
        logger.error(f"Failed to set runtime cap: {e}")
        raise RuntimeError(f"Failed to set runtime cap: {e}")

    return seconds

def get_env_config() -> dict:
    """
    Returns a dictionary of the current environment configuration.
    """
    return {
        "available_memory_gb": get_available_memory_gb(),
        "memory_limit_gb": os.getenv('LLMXIVE_MEMORY_LIMIT_GB', str(DEFAULT_MEMORY_LIMIT_GB)),
        "runtime_cap_seconds": os.getenv('LLMXIVE_RUNTIME_CAP_SECONDS', str(DEFAULT_RUNTIME_CAP_SECONDS)),
        "platform": sys.platform
    }

def main():
    """
    CLI entry point for testing environment configuration.
    """
    print("=== Environment Configuration Check ===")
    try:
        is_valid, avail = check_memory_limit()
        print(f"Memory Check: PASS (Available: {avail:.2f} GB)")
    except RuntimeError as e:
        print(f"Memory Check: FAIL - {e}")
        sys.exit(1)

    cap = set_runtime_cap()
    if cap > 0:
        print(f"Runtime Cap: Set to {cap} seconds")
    else:
        print("Runtime Cap: Not set (OS limitation or skipped)")

    print("=== Config Summary ===")
    config = get_env_config()
    for k, v in config.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()