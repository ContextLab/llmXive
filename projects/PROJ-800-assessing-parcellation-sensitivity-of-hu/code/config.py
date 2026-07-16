"""
Configuration manager for the llmXive pipeline.

Handles paths, random seeds, and specific parameters for hub definition
and sensitivity analysis as required by the project specification.
"""

import os
from pathlib import Path
from typing import List, Set, Dict, Any

from utils.logger import ConfigurationError, get_logger

logger = get_logger(__name__)

# Project Root (assumed to be the directory containing 'code/')
# We traverse up from this file's location to find the root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Path Configuration ---
PATHS: Dict[str, Path] = {
    "root": _PROJECT_ROOT,
    "data_raw": _PROJECT_ROOT / "data" / "raw",
    "data_processed": _PROJECT_ROOT / "data" / "processed",
    "data_results": _PROJECT_ROOT / "data" / "results",
    "code": _PROJECT_ROOT / "code",
    "tests": _PROJECT_ROOT / "tests",
    "specs": _PROJECT_ROOT / "specs",
}

# --- Random Seed Configuration ---
# Pinned seed for reproducibility across the pipeline
RANDOM_SEED: int = 42

# --- Hub Definition Configuration ---
# Fixed default threshold for identifying hubs (top 10% nodes)
# Used by T023 to determine hub count: floor(N * default_hub_threshold)
DEFAULT_HUB_THRESHOLD: float = 0.10

# --- Sensitivity Analysis Configuration ---
# Values for the threshold sweep as explicitly defined in T006
# Used by T033 to perform sensitivity analysis across multiple thresholds
SENSITIVITY_SWEEP_VALUES: Set[float] = {0.08, 0.10, 0.12}

# --- Atlas Configuration ---
# Mapping of resolution names to expected node counts for validation
ATLAS_NODE_COUNTS: Dict[str, int] = {
    "aal90": 90,
    "schaefer200": 200,
    "schaefer400": 400,
}

# --- File Patterns ---
# Patterns used to identify generated artifacts
OUTPUT_MATRIX_PATTERN = "{subject}_{resolution}.npz"
OUTPUT_CENTRALITY_PATTERN = "{subject}_{resolution}_centrality.csv"
OUTPUT_PERMUTATION_PATTERN = "permutation_pvalue.csv"
OUTPUT_SENSITIVITY_PATTERN = "sensitivity_sweep.csv"

def get_path(key: str) -> Path:
    """
    Retrieve a configured path by key.

    Args:
        key: One of 'root', 'data_raw', 'data_processed', 'data_results',
             'code', 'tests', 'specs'.

    Returns:
        The Path object if it exists in PATHS.

    Raises:
        ConfigurationError: If the key is unknown.
    """
    if key not in PATHS:
        raise ConfigurationError(f"Unknown path key: {key}. Available keys: {list(PATHS.keys())}")
    return PATHS[key]

def ensure_paths_exist() -> None:
    """
    Ensure all configured data and result directories exist on disk.
    Creates them if they are missing.
    """
    logger.info("Ensuring project directory structure exists...")
    for path_name, path_obj in PATHS.items():
        if path_name in ["code", "tests", "specs"]:
            # These are source directories, usually exist, but ensure just in case
            continue
        
        if not path_obj.exists():
            logger.info(f"Creating directory: {path_obj}")
            path_obj.mkdir(parents=True, exist_ok=True)
    
    logger.info("Directory structure verified.")

def get_sensitivity_thresholds() -> List[float]:
    """
    Returns the sorted list of sensitivity sweep values.
    
    Returns:
        A sorted list of floats: [0.08, 0.10, 0.12]
    """
    return sorted(list(SENSITIVITY_SWEEP_VALUES))

def get_hub_threshold() -> float:
    """
    Returns the default hub threshold.
    
    Returns:
        The float value 0.10.
    """
    return DEFAULT_HUB_THRESHOLD

# Immediate validation on import to catch path issues early
# Only run if this module is imported directly or via a runner that expects initialization
# We do not auto-create directories on import to avoid side-effects in test environments
# unless explicitly called.

if __name__ == "__main__":
    # Simple test runner to verify configuration
    print("Project Root:", get_path("root"))
    print("Data Raw:", get_path("data_raw"))
    print("Hub Threshold:", get_hub_threshold())
    print("Sweep Values:", get_sensitivity_thresholds())
    ensure_paths_exist()
    print("Configuration initialized successfully.")
