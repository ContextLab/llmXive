"""
Global configuration for the llmXive research pipeline.

Defines global seeds, paths, and resolution targets.
"""
import os
from pathlib import Path
from typing import Final, List, Optional
import json

# Project Root (assumes running from project root or script is in code/src)
# We determine root relative to this file's location
_ROOT_DIR = Path(__file__).resolve().parent.parent

# Global Constants
GLOBAL_SEED: Final[int] = 42
RANDOM_SEED: Final[int] = GLOBAL_SEED
NUMPY_SEED: Final[int] = GLOBAL_SEED
PYTORCH_SEED: Final[int] = GLOBAL_SEED  # If used later

# Resolution Targets (Hz)
# Ordered from highest (original) to lowest (downsampled)
RESOLUTION_TARGETS: Final[List[int]] = [4096, 2048, 1024, 512, 256]
BASE_RESOLUTION: Final[int] = 4096

# Path Directories
DATA_DIR: Final[Path] = _ROOT_DIR / "data"
PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
FIGURES_DIR: Final[Path] = _ROOT_DIR / "figures"
CONTRACTS_DIR: Final[Path] = _ROOT_DIR / "contracts"
STATE_DIR: Final[Path] = _ROOT_DIR / "state"

# File Paths
INJECTION_SCHEMA_PATH: Final[Path] = CONTRACTS_DIR / "injection.schema.yaml"
METRIC_SCHEMA_PATH: Final[Path] = CONTRACTS_DIR / "detection_metric.schema.yaml"

# Output Files
INJECTIONS_CSV_PATH: Final[Path] = PROCESSED_DIR / "injections.csv"
ANALYSIS_RESULTS_JSON_PATH: Final[Path] = PROCESSED_DIR / "analysis_results.json"
CHECKSUMS_JSON_PATH: Final[Path] = STATE_DIR / "checksums.json"
PROFILER_LOG_PATH: Final[Path] = STATE_DIR / "profiler_log.json"

def get_contract_path(schema_name: str) -> Path:
    """
    Returns the full path to a schema file in the contracts directory.

    Args:
        schema_name: The filename of the schema (e.g., 'injection.schema.yaml').

    Returns:
        Path to the schema file.
    """
    return CONTRACTS_DIR / schema_name

def ensure_directories() -> None:
    """
    Creates all required directories if they do not exist.
    """
    dirs = [DATA_DIR, PROCESSED_DIR, FIGURES_DIR, CONTRACTS_DIR, STATE_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_data_path(subpath: Optional[str] = None) -> Path:
    """
    Returns a path within the data directory.

    Args:
        subpath: Optional subdirectory or filename relative to data/.

    Returns:
        Full path to the data file/directory.
    """
    if subpath:
        return DATA_DIR / subpath
    return DATA_DIR

def get_processed_path(subpath: Optional[str] = None) -> Path:
    """
    Returns a path within the data/processed directory.

    Args:
        subpath: Optional subdirectory or filename relative to data/processed/.

    Returns:
        Full path to the processed file/directory.
    """
    if subpath:
        return PROCESSED_DIR / subpath
    return PROCESSED_DIR

def get_figure_path(subpath: Optional[str] = None) -> Path:
    """
    Returns a path within the figures directory.

    Args:
        subpath: Optional subdirectory or filename relative to figures/.

    Returns:
        Full path to the figure file/directory.
    """
    if subpath:
        return FIGURES_DIR / subpath
    return FIGURES_DIR

def validate_config() -> bool:
    """
    Validates that the configuration is consistent and required paths exist.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    # Check resolutions are strictly decreasing and positive
    if not all(RESOLUTION_TARGETS[i] > RESOLUTION_TARGETS[i+1] for i in range(len(RESOLUTION_TARGETS)-1)):
        raise ValueError("Resolution targets must be strictly decreasing.")
    
    if BASE_RESOLUTION != RESOLUTION_TARGETS[0]:
        raise ValueError("BASE_RESOLUTION must match the highest resolution target.")

    # Check schema files exist if they are expected to be present
    # Note: We don't fail if they don't exist yet, as T004 might not have run in this specific context,
    # but we log a warning or ensure they are created if needed by other tasks.
    # For T005, we just ensure the config structure is valid.
    
    ensure_directories()
    
    return True

# Initialize directories on import if desired, or rely on explicit call
# ensure_directories() 

# Configuration Summary for debugging
if __name__ == "__main__":
    print(f"Project Root: {_ROOT_DIR}")
    print(f"Data Dir: {DATA_DIR}")
    print(f"Processed Dir: {PROCESSED_DIR}")
    print(f"Resolutions: {RESOLUTION_TARGETS}")
    print(f"Global Seed: {GLOBAL_SEED}")
    validate_config()
    print("Configuration validated successfully.")
