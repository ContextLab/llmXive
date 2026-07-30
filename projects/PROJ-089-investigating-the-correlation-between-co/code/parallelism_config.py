"""
Configuration for parallel processing limits in the research pipeline.

This module provides constants and utilities to constrain the number of
concurrent repository processes, preventing resource exhaustion during
data extraction and static analysis phases.
"""
import os
from typing import Optional

# Default concurrency limits
# These values are chosen to balance throughput with system stability
# on standard research compute nodes (approx. 8-16 cores, 16-32GB RAM)
DEFAULT_MAX_CONCURRENT_REPOS: int = 4
DEFAULT_MAX_CONCURRENT_FILES: int = 8

# Environment variable names for configuration override
ENV_VAR_MAX_CONCURRENT_REPOS: str = "LLMXIVE_MAX_CONCURRENT_REPOS"
ENV_VAR_MAX_CONCURRENT_FILES: str = "LLMXIVE_MAX_CONCURRENT_FILES"

def get_max_concurrent_repos() -> int:
    """
    Get the maximum number of concurrent repository processes.

    Reads from environment variable if set, otherwise returns default.
    Ensures the value is at least 1.

    Returns:
        int: The maximum number of concurrent repo processes.
    """
    env_val = os.getenv(ENV_VAR_MAX_CONCURRENT_REPOS)
    if env_val:
        try:
            val = int(env_val)
            return max(1, val)
        except ValueError:
            # Log warning or fallback if needed, but for now just return default
            pass
    return DEFAULT_MAX_CONCURRENT_REPOS

def get_max_concurrent_files() -> int:
    """
    Get the maximum number of concurrent file-level analysis processes.

    Reads from environment variable if set, otherwise returns default.
    Ensures the value is at least 1.

    Returns:
        int: The maximum number of concurrent file processes.
    """
    env_val = os.getenv(ENV_VAR_MAX_CONCURRENT_FILES)
    if env_val:
        try:
            val = int(env_val)
            return max(1, val)
        except ValueError:
            pass
    return DEFAULT_MAX_CONCURRENT_FILES

def update_config_with_limits() -> None:
    """
    Update the global config or environment to enforce concurrency limits.
    
    This function can be called at the start of pipeline execution to
    ensure that downstream modules respect the configured limits.
    It sets the environment variables if they aren't already set, 
    establishing a consistent limit for worker processes.
    """
    if ENV_VAR_MAX_CONCURRENT_REPOS not in os.environ:
        os.environ[ENV_VAR_MAX_CONCURRENT_REPOS] = str(get_max_concurrent_repos())
    if ENV_VAR_MAX_CONCURRENT_FILES not in os.environ:
        os.environ[ENV_VAR_MAX_CONCURRENT_FILES] = str(get_max_concurrent_files())
