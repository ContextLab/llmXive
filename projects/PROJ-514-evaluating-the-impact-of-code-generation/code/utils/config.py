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
    "temp_dir": PROJECT_ROOT / "temp_clones"
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
