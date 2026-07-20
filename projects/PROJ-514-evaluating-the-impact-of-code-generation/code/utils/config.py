"""
Environment configuration management.
Handles seeds, paths, timeouts, API keys.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Default configuration
DEFAULT_CONFIG = {
    "random_seed": 42,
    "github_api_timeout": 30,
    "git_clone_timeout": 300,
    "pmd_memory_limit_gb": 2,
    "pmd_timeout_seconds": 120,
    "max_retries": 3,
    "retry_delay_seconds": 5,
    "output_dir": PROJECT_ROOT / "data",
    "reports_dir": PROJECT_ROOT / "reports",
    "logs_dir": PROJECT_ROOT / "logs",
    "temp_dir": PROJECT_ROOT / "temp_clones",
    # API Keys (must be set via environment variables in production)
    "github_token": None,
    "huggingface_token": None,
    "pmd_home": None,
    "java_home": None
}

def get_project_root() -> Path:
    """Get the project root directory."""
    return PROJECT_ROOT

def get_config(key: Optional[str] = None) -> Any:
    """
    Get configuration value.
    
    Args:
        key: Specific config key to retrieve, or None for full config
    
    Returns:
        Configuration value or full config dict
    """
    # Check environment variables first
    env_key = key.upper() if key else None
    if env_key and env_key in os.environ:
        return os.environ[env_key]
    
    if key:
        return DEFAULT_CONFIG.get(key)
    return DEFAULT_CONFIG.copy()

def validate_config() -> Dict[str, Any]:
    """
    Validate that critical configuration is present.
    Returns a dict of missing critical keys and their status.
    
    Returns:
        Dict with 'valid' boolean and 'missing_keys' list
    """
    missing_keys = []
    
    # Check for API tokens if needed by data collection
    # We don't fail here, just warn - actual checks happen in the modules that use them
    if get_config("github_token") is None:
        missing_keys.append("GITHUB_TOKEN")
    
    # Check for PMD/Java if needed by static analysis
    if get_config("pmd_home") is None:
        missing_keys.append("PMD_HOME")
        
    if get_config("java_home") is None:
        missing_keys.append("JAVA_HOME")
    
    return {
        "valid": len(missing_keys) == 0,
        "missing_keys": missing_keys,
        "config": get_config()
    }

def get_output_paths() -> Dict[str, Path]:
    """
    Get all output directory paths as a dictionary.
    
    Returns:
        Dict with keys: 'raw', 'intermediate', 'processed', 'reports', 'logs'
    """
    output_dir = get_config("output_dir")
    return {
        "raw": output_dir / "raw",
        "intermediate": output_dir / "intermediate",
        "processed": output_dir / "processed",
        "reports": get_config("reports_dir"),
        "logs": get_config("logs_dir")
    }

def get_timeouts() -> Dict[str, int]:
    """
    Get timeout configuration values.
    
    Returns:
        Dict with keys: 'github_api', 'git_clone', 'pmd'
    """
    return {
        "github_api": get_config("github_api_timeout"),
        "git_clone": get_config("git_clone_timeout"),
        "pmd": get_config("pmd_timeout_seconds")
    }

def get_limits() -> Dict[str, Any]:
    """
    Get resource limit configuration values.
    
    Returns:
        Dict with keys: 'pmd_memory_gb', 'max_retries', 'retry_delay_seconds'
    """
    return {
        "pmd_memory_gb": get_config("pmd_memory_limit_gb"),
        "max_retries": get_config("max_retries"),
        "retry_delay_seconds": get_config("retry_delay_seconds")
    }

def get_random_seed() -> int:
    """
    Get the random seed for reproducibility.
    
    Returns:
        Random seed integer
    """
    return get_config("random_seed")

def ensure_directories_exist() -> bool:
    """
    Ensure all required output directories exist.
    
    Returns:
        True if all directories were created or already existed
    """
    paths = get_output_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return True