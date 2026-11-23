"""
Configuration for batch processing constraints.
Centralizes RAM and time limits for T025.
"""
import os

# Memory limit in GB
RAM_LIMIT_GB = float(os.getenv("RAM_LIMIT_GB", "7.0"))

# Time limit in hours
TIME_LIMIT_HOURS = float(os.getenv("TIME_LIMIT_HOURS", "4.0"))

# Batch size for processing
DEFAULT_BATCH_SIZE = int(os.getenv("DEFAULT_BATCH_SIZE", "10"))

# Memory check interval (number of batches)
MEMORY_CHECK_INTERVAL = int(os.getenv("MEMORY_CHECK_INTERVAL", "5"))

def get_config() -> dict:
    """Return current batch processing configuration."""
    return {
        "ram_limit_gb": RAM_LIMIT_GB,
        "time_limit_hours": TIME_LIMIT_HOURS,
        "batch_size": DEFAULT_BATCH_SIZE,
        "memory_check_interval": MEMORY_CHECK_INTERVAL
    }
