"""
Environment configuration management for local vs. CI paths.

This module provides a unified interface to determine the execution environment
(Local or CI) and returns appropriate base paths and resource limits.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Constants for environment detection
CI_ENV_VARS = [
    'CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'CIRCLECI', 'TRAVIS', 
    'JENKINS_URL', 'TEAMCITY_VERSION', 'BUILD_NUMBER'
]

# Default paths relative to project root
DEFAULT_BASE_PATH = Path.cwd()

# Resource limits based on environment
CI_RESOURCE_LIMITS = {
    'max_memory_mb': 14000,
    'max_disk_gb': 50,
    'timeout_seconds': 3600,
    'max_workers': 4
}

LOCAL_RESOURCE_LIMITS = {
    'max_memory_mb': 32000,
    'max_disk_gb': 100,
    'timeout_seconds': 7200,
    'max_workers': 8
}

_base_path: Optional[Path] = None
_is_ci: Optional[bool] = None
_resource_limits: Optional[Dict[str, Any]] = None

def is_ci_environment() -> bool:
    """
    Detect if the code is running in a CI environment.
    
    Returns:
        bool: True if running in CI, False otherwise.
    """
    global _is_ci
    if _is_ci is not None:
        return _is_ci
    
    _is_ci = any(os.environ.get(var) for var in CI_ENV_VARS)
    
    # Explicit override via environment variable
    if os.environ.get('FORCE_CI_ENV') == 'true':
        _is_ci = True
    elif os.environ.get('FORCE_LOCAL_ENV') == 'true':
        _is_ci = False
        
    return _is_ci

def set_base_path(path: Optional[Path] = None) -> None:
    """
    Set the global base path for the project.
    
    Args:
        path: Optional explicit path. If None, uses cwd or CI workspace.
    """
    global _base_path
    if path is not None:
        _base_path = Path(path).resolve()
    elif is_ci_environment():
        # CI often sets WORKSPACE or similar
        _base_path = Path(os.environ.get('GITHUB_WORKSPACE', 
                       os.environ.get('WORKSPACE', 
                       DEFAULT_BASE_PATH))).resolve()
    else:
        _base_path = DEFAULT_BASE_PATH

def get_base_path() -> Path:
    """
    Get the current base path for the project.
    
    Returns:
        Path: The resolved base path.
    """
    global _base_path
    if _base_path is None:
        set_base_path()
    return _base_path

def _get_env_specific_path(relative_path: str) -> Path:
    """
    Construct an absolute path based on the environment.
    
    Args:
        relative_path: Relative path from base directory.
        
    Returns:
        Path: Absolute path.
    """
    base = get_base_path()
    full_path = base / relative_path
    
    # Ensure the directory exists (create if missing)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    return full_path

def get_data_path() -> Path:
    """Get the base data directory."""
    return _get_env_specific_path("data")

def get_raw_data_path() -> Path:
    """Get the raw data directory."""
    return _get_env_specific_path("data/raw")

def get_processed_data_path() -> Path:
    """Get the processed data directory."""
    return _get_env_specific_path("data/processed")

def get_logs_path() -> Path:
    """Get the logs directory."""
    return _get_env_specific_path("data/logs")

def get_reports_path() -> Path:
    """Get the reports directory."""
    return _get_env_specific_path("reports")

def get_state_path() -> Path:
    """Get the state directory."""
    return _get_env_specific_path("state")

def get_specs_path() -> Path:
    """Get the specs directory."""
    return _get_env_specific_path("specs")

def get_resource_limits() -> Dict[str, Any]:
    """
    Get resource limits based on the current environment.
    
    Returns:
        Dict[str, Any]: Resource limits configuration.
    """
    global _resource_limits
    if _resource_limits is not None:
        return _resource_limits
    
    if is_ci_environment():
        _resource_limits = CI_RESOURCE_LIMITS
    else:
        _resource_limits = LOCAL_RESOURCE_LIMITS
      
    # Allow override via environment variables
    if os.environ.get('RESOURCE_LIMITS'):
        import json
        try:
            _resource_limits = json.loads(os.environ['RESOURCE_LIMITS'])
        except (json.JSONDecodeError, TypeError):
            pass # Fallback to defaults
            
    return _resource_limits

def set_global_seed(seed: int = 42) -> None:
    """
    Set a global random seed for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    import random
    import numpy as np
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Log the seed for traceability
    logger = setup_logger()
    if logger:
        logger.info(f"Global seed set to {seed} (Environment: {'CI' if is_ci_environment() else 'Local'})")

def ensure_dirs() -> None:
    """
    Ensure all required directories exist.
    Creates directories if they don't exist based on current environment.
    """
    paths = [
        get_data_path(),
        get_raw_data_path(),
        get_processed_data_path(),
        get_logs_path(),
        get_reports_path(),
        get_state_path(),
        get_specs_path(),
        Path.cwd() / "code",
        Path.cwd() / "tests"
    ]
    
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def setup_logger() -> Optional[Any]:
    """
    Setup a basic logger for the pipeline.
    
    Returns:
        Optional[logging.Logger]: Logger instance or None.
    """
    import logging
    from pathlib import Path
    
    log_dir = get_logs_path()
    log_file = log_dir / f"pipeline_{is_ci_environment()}.log"
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# Initialize module on import
set_base_path()
