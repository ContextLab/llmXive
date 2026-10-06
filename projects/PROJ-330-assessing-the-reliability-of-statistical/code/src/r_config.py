"""
R Environment Configuration Management.

This module provides configuration for R script execution paths and memory limits.
It reads from a YAML configuration file and exposes validated settings for the
pipeline to use when invoking R subprocesses.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import logging

from src.config import PROJECT_ROOT

# Default configuration paths
R_CONFIG_FILE: Path = PROJECT_ROOT / "code" / "config" / "r_config.yaml"
DEFAULT_R_SCRIPT_DIR: Path = PROJECT_ROOT / "code" / "scripts"
DEFAULT_MEMORY_LIMIT_MB: int = 4096  # 4GB default limit
DEFAULT_TIME_LIMIT_SECONDS: int = 3600  # 1 hour default limit

logger = logging.getLogger(__name__)


def load_r_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load R configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file. Defaults to R_CONFIG_FILE.

    Returns:
        Dictionary containing R configuration settings.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file contains invalid YAML.
    """
    if config_path is None:
        config_path = R_CONFIG_FILE

    if not config_path.exists():
        logger.warning(f"R config file not found at {config_path}, using defaults")
        return {
            "r_script_dir": str(DEFAULT_R_SCRIPT_DIR),
            "memory_limit_mb": DEFAULT_MEMORY_LIMIT_MB,
            "time_limit_seconds": DEFAULT_TIME_LIMIT_SECONDS,
            "r_executable": "Rscript",
            "additional_env": {}
        }

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate and set defaults for missing keys
    validated_config = {
        "r_script_dir": config.get("r_script_dir", str(DEFAULT_R_SCRIPT_DIR)),
        "memory_limit_mb": config.get("memory_limit_mb", DEFAULT_MEMORY_LIMIT_MB),
        "time_limit_seconds": config.get("time_limit_seconds", DEFAULT_TIME_LIMIT_SECONDS),
        "r_executable": config.get("r_executable", "Rscript"),
        "additional_env": config.get("additional_env", {})
    }

    # Ensure paths are absolute
    validated_config["r_script_dir"] = str(Path(validated_config["r_script_dir"]).resolve())

    return validated_config


def get_r_script_path(script_name: str, config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get the full path to an R script.

    Args:
        script_name: Name of the R script file.
        config: Optional config dictionary. If None, loads from default location.

    Returns:
        Path object pointing to the R script.

    Raises:
        FileNotFoundError: If the script does not exist.
    """
    if config is None:
        config = load_r_config()

    script_dir = Path(config["r_script_dir"])
    script_path = script_dir / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"R script not found: {script_path}")

    return script_path


def get_memory_limit_mb(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the memory limit for R processes in megabytes.

    Args:
        config: Optional config dictionary. If None, loads from default location.

    Returns:
        Memory limit in megabytes.
    """
    if config is None:
        config = load_r_config()

    return int(config["memory_limit_mb"])


def get_time_limit_seconds(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the time limit for R processes in seconds.

    Args:
        config: Optional config dictionary. If None, loads from default location.

    Returns:
        Time limit in seconds.
    """
    if config is None:
        config = load_r_config()

    return int(config["time_limit_seconds"])


def get_r_executable(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the path/name of the R executable to use.

    Args:
        config: Optional config dictionary. If None, loads from default location.

    Returns:
        String path/name of R executable.
    """
    if config is None:
        config = load_r_config()

    return config["r_executable"]


def get_r_env_vars(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Get environment variables to set for R processes.

    Args:
        config: Optional config dictionary. If None, loads from default location.

    Returns:
        Dictionary of environment variables.
    """
    if config is None:
        config = load_r_config()

    env_vars = dict(os.environ)
    env_vars.update(config.get("additional_env", {}))

    # Set memory limit as environment variable for R
    memory_mb = get_memory_limit_mb(config)
    env_vars["R_MAX_VSIZE"] = f"{memory_mb * 1024 * 1024}"  # Convert MB to bytes

    return env_vars


def create_default_config(output_path: Optional[Path] = None) -> Path:
    """
    Create a default R configuration file.

    Args:
        output_path: Path where to write the config. Defaults to R_CONFIG_FILE.

    Returns:
        Path to the created config file.
    """
    if output_path is None:
        output_path = R_CONFIG_FILE

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    default_config = {
        "# R Script Configuration": "Directory containing R scripts",
        "r_script_dir": str(DEFAULT_R_SCRIPT_DIR),
        "# Memory Configuration": "Maximum memory (MB) for R processes",
        "memory_limit_mb": DEFAULT_MEMORY_LIMIT_MB,
        "# Time Configuration": "Maximum execution time (seconds) for R processes",
        "time_limit_seconds": DEFAULT_TIME_LIMIT_SECONDS,
        "# R Executable": "Path to Rscript executable (use full path if not in PATH)",
        "r_executable": "Rscript",
        "# Additional Environment": "Extra environment variables for R processes",
        "additional_env": {
            "R_LIBS_USER": str(PROJECT_ROOT / "code" / "R_libs")
        }
    }

    with open(output_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Created default R config at {output_path}")
    return output_path


def validate_r_environment(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate that the R environment is properly configured.

    Args:
        config: Optional config dictionary. If None, loads from default location.

    Returns:
        True if environment is valid, False otherwise.
    """
    if config is None:
        config = load_r_config()

    # Check if R executable exists
    import shutil
    r_executable = get_r_executable(config)
    if shutil.which(r_executable) is None:
        logger.error(f"R executable not found: {r_executable}")
        return False

    # Check if script directory exists
    script_dir = Path(config["r_script_dir"])
    if not script_dir.exists():
        logger.error(f"R script directory does not exist: {script_dir}")
        return False

    # Check memory limit is reasonable
    memory_mb = get_memory_limit_mb(config)
    if memory_mb < 512:
        logger.warning(f"Memory limit is very low: {memory_mb}MB")

    return True