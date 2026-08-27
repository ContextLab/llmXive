"""
Main package for MOND analysis pipeline.
Exports core utilities and configuration loaders.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Import utilities from sibling modules
from .utils import (
    setup_logging,
    get_logger,
    log_stage,
    set_global_seed,
    get_timestamp,
    safe_divide,
    format_number,
    ensure_directory,
    calculate_chi2,
    calculate_aic,
    calculate_bic,
)
from .download import (
    fetch_with_retry,
    download_file,
    validate_url,
    is_valid_sparc_source,
    verify_file_integrity,
    download_sparc_data,
)
from .preprocess import (
    parse_sparc_file,
    parse_galaxy_directory,
    apply_quality_filters,
    extract_rotation_curves,
    main as preprocess_main,
)

__all__ = [
    # Utils
    "setup_logging",
    "get_logger",
    "log_stage",
    "set_global_seed",
    "get_timestamp",
    "safe_divide",
    "format_number",
    "ensure_directory",
    "calculate_chi2",
    "calculate_aic",
    "calculate_bic",
    # Download
    "fetch_with_retry",
    "download_file",
    "validate_url",
    "is_valid_sparc_source",
    "verify_file_integrity",
    "download_sparc_data",
    # Preprocess
    "parse_sparc_file",
    "parse_galaxy_directory",
    "apply_quality_filters",
    "extract_rotation_curves",
    "preprocess_main",
    # Local functions
    "load_config",
    "get_config",
    "create_default_metadata",
    "ensure_dirs",
]

# --- Configuration Loader Implementation (T005) ---

_CONFIG_CACHE: Optional[Dict[str, Any]] = None
_CONFIG_PATH: Optional[Path] = None


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from data/metadata.yaml.
    
    Args:
        config_path: Optional path to config file. Defaults to 'data/metadata.yaml'.
        
    Returns:
        Dictionary containing the loaded configuration.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If file is not valid YAML.
    """
    global _CONFIG_CACHE, _CONFIG_PATH
    
    if config_path is None:
        config_path = "data/metadata.yaml"
    
    path = Path(config_path)
    
    # Return cached config if path hasn't changed
    if _CONFIG_CACHE is not None and _CONFIG_PATH == path:
        return _CONFIG_CACHE
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    _CONFIG_CACHE = config
    _CONFIG_PATH = path
    return config


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration, loading it if necessary.
    
    Returns:
        The configuration dictionary.
    """
    return load_config()


def create_default_metadata() -> Dict[str, Any]:
    """
    Create a default metadata structure for a new run.
    
    Returns:
        Default metadata dictionary.
    """
    from datetime import datetime
    return {
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "source": "SPARC",
        "filters": {
            "inclination_max": 90.0,
            "points_min": 15,
            "inclination_uncertainty_max": 10.0
        }
    }


def ensure_dirs() -> None:
    """
    Ensure all required directories exist.
    """
    dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "results",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "state",
        "contracts",
    ]
    for d in dirs:
        ensure_directory(d)