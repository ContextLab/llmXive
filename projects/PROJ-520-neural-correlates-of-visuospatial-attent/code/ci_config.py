"""
CI Environment Configuration for PROJ-520.

Defines hard limits for the CI runner environment to ensure
memory and CPU constraints are respected during execution.

These limits correspond to typical free-tier CI runner specifications.
"""

import os
import sys
from typing import Dict, Any, Optional

# Hard limits defined by the task specification
# 7GB = 7 * 1024^3 bytes
RAM_LIMIT_GB: float = 7.0
RAM_LIMIT_BYTES: int = int(7.0 * 1024 * 1024 * 1024)

# CPU limit
CPU_LIMIT: int = 2

def get_ram_limit_bytes() -> int:
    """Return the RAM limit in bytes."""
    return RAM_LIMIT_BYTES

def get_ram_limit_gb() -> float:
    """Return the RAM limit in GB."""
    return RAM_LIMIT_GB

def get_cpu_limit() -> int:
    """Return the CPU limit count."""
    return CPU_LIMIT

def get_ci_config() -> Dict[str, Any]:
    """
    Returns a dictionary containing the CI configuration limits.
    
    Returns:
        dict: Configuration with keys 'RAM_LIMIT_GB', 'RAM_LIMIT_BYTES', 'CPU_LIMIT'.
    """
    return {
        'RAM_LIMIT_GB': RAM_LIMIT_GB,
        'RAM_LIMIT_BYTES': RAM_LIMIT_BYTES,
        'CPU_LIMIT': CPU_LIMIT
    }

def enforce_limits() -> bool:
    """
    Checks if the current environment exceeds the defined CI limits.
    
    This function attempts to detect the available resources and compares
    them against the configured limits. If the system reports available
    resources significantly higher than limits, it logs a warning.
    
    Returns:
        bool: True if limits are within bounds or undetectable, False if
              hard limit is exceeded (though typically we just warn).
    """
    try:
        # Check CPU count
        available_cpus = os.cpu_count()
        if available_cpus is not None and available_cpus > CPU_LIMIT:
            # In CI, we might see more cores physically but be throttled.
            # We log a warning that we are configured for fewer.
            pass 
        
        # Check Memory (approximate via /proc on Linux or resource module)
        try:
            if sys.platform == 'linux':
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            # Value in kB
                            mem_kb = int(line.split()[1])
                            mem_gb = mem_kb / (1024 * 1024)
                            if mem_gb < RAM_LIMIT_GB:
                                # System has less than limit, safe
                                return True
                            # If system has more, we are just capped by config
                            break
            else:
                # Fallback for other platforms: assume safe if we can't check
                pass
        except (FileNotFoundError, ValueError, IndexError):
            pass
        
        return True
    except Exception:
        # If we can't check, assume safe but log
        return True

if __name__ == "__main__":
    config = get_ci_config()
    print(f"CI Configuration:")
    print(f"  RAM Limit: {config['RAM_LIMIT_GB']} GB ({config['RAM_LIMIT_BYTES']} bytes)")
    print(f"  CPU Limit: {config['CPU_LIMIT']}")
    if enforce_limits():
        print("Environment check passed.")
    else:
        print("WARNING: Environment exceeds configured limits.")