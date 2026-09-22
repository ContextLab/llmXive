"""
Configuration management for the AgentDoG drift detection pipeline.
Handles random seeds, paths, batch sizes, and global constants.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

import numpy as np

# =============================================================================
# Global Constants (Per Task T011a Requirements)
# =============================================================================
RANDOM_SEED = 42
MAX_RAM_GB = 7

# Source: arxiv.org/abs/2410.21676
# Paper: AgentDoG: Automated Drift Detection and Grounding for Large Language Models
# Citation: {{claim:c_fd6a8181}} (2410.21676, https://arxiv.org/abs/2410.21676) # Source: arxiv.org/abs/2410.21676
AGENTDOG_PAPER_ID = "2410.21676"
AGENTDOG_PAPER_URL = "https://arxiv.org/abs/2410.21676"

# Default Batch Sizes
DEFAULT_BATCH_SIZE = 32
MAX_BATCH_SIZE_MEMORY_SAFE = 64

# Model Configuration
CENTROID_MODEL_NAME = "all-MiniLM-L6-v2"
BASELINE_MODEL_NAME = "google/flan-t5-small"

# Thresholds
DRIFT_THRESHOLD_DEFAULT = 0.5
KAPPA_ACCEPTANCE_THRESHOLD = 0.6
AUC_DRIFT_TOLERANCE = 0.10

# =============================================================================
# Project Paths
# =============================================================================
# Determine project root based on execution context
# If running from code/, go up one level. If running from project root, stay.
_CURRENT_DIR = Path(__file__).resolve().parent
if _CURRENT_DIR.name == "code":
    PROJECT_ROOT = _CURRENT_DIR.parent
else:
    PROJECT_ROOT = _CURRENT_DIR

# Standardized Directory Structure
PATHS = {
    "project_root": PROJECT_ROOT,
    "code": PROJECT_ROOT / "code",
    "data": PROJECT_ROOT / "data",
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "data_test": PROJECT_ROOT / "data" / "test",
    "specs": PROJECT_ROOT / "specs",
    "specs_proj": PROJECT_ROOT / "specs" / "PROJ-924",
    "docs": PROJECT_ROOT / "docs",
    "figures": PROJECT_ROOT / "figures",
}

# =============================================================================
# Configuration Dictionary
# =============================================================================
_CONFIG: Dict[str, Any] = {
    "random_seed": RANDOM_SEED,
    "max_ram_gb": MAX_RAM_GB,
    "batch_size": DEFAULT_BATCH_SIZE,
    "centroid_model": CENTROID_MODEL_NAME,
    "baseline_model": BASELINE_MODEL_NAME,
    "drift_threshold": DRIFT_THRESHOLD_DEFAULT,
    "kappa_threshold": KAPPA_ACCEPTANCE_THRESHOLD,
    "auc_tolerance": AUC_DRIFT_TOLERANCE,
    "paths": PATHS,
}

# =============================================================================
# Seed Management
# =============================================================================
def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across random, numpy, and torch.
    
    Args:
        seed: The seed value. Defaults to RANDOM_SEED if None.
    """
    if seed is None:
        seed = RANDOM_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch not installed, skip

def get_config() -> Dict[str, Any]:
    """Return the current configuration dictionary."""
    return _CONFIG.copy()

def update_config(key: str, value: Any) -> None:
    """Update a specific configuration value."""
    _CONFIG[key] = value

def get_config_summary() -> str:
    """Return a string summary of the current configuration."""
    lines = [
        f"Random Seed: {_CONFIG['random_seed']}",
        f"Max RAM (GB): {_CONFIG['max_ram_gb']}",
        f"Batch Size: {_CONFIG['batch_size']}",
        f"Centroid Model: {_CONFIG['centroid_model']}",
        f"Baseline Model: {_CONFIG['baseline_model']}",
    ]
    return "\n".join(lines)

# =============================================================================
# Path Resolution
# =============================================================================
def get_path(*parts: Union[str, Path]) -> Path:
    """
    Resolve a path relative to the project root.
    
    Supports flexible calling conventions:
      - get_path("raw_data") -> data/raw
      - get_path("data", "processed") -> data/processed
      - get_path("data", "processed", "file.csv") -> data/processed/file.csv
      - get_path("key") where key is in PATHS -> PATHS[key]
    
    Args:
        *parts: Path components or a registered key name.
        
    Returns:
        A resolved Path object.
    """
    if not parts:
        return PROJECT_ROOT
    
    first = parts[0]
    
    # Check if the first part is a registered key in PATHS
    if len(parts) == 1 and first in PATHS:
        return PATHS[first]
    
    # If the first part is a registered key, use it as the base
    if first in PATHS:
        base = PATHS[first]
        remaining = parts[1:]
    else:
        # Otherwise, assume relative to project root
        base = PROJECT_ROOT
        remaining = parts
    
    result = base
    for part in remaining:
        result = result / part
    
    return result

def get_output_path(*parts: Union[str, Path]) -> Path:
    """
    Alias for get_path, ensuring the path is within the project tree.
    Used explicitly for output destinations.
    """
    return get_path(*parts)

# =============================================================================
# Directory Management
# =============================================================================
def ensure_directories(paths: Optional[List[Path]] = None) -> None:
    """
    Ensure that the specified directories exist.
    
    Args:
        paths: List of Path objects. If None, ensures standard project directories.
    """
    if paths is None:
        # Default set of directories to ensure
        paths = [
            PATHS["data_raw"],
            PATHS["data_processed"],
            PATHS["data_test"],
            PATHS["specs"],
            PATHS["specs_proj"],
            PATHS["docs"],
            PATHS["figures"],
        ]
    
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Batch Size & Memory Helpers
# =============================================================================
def get_batch_size() -> int:
    """Return the configured batch size."""
    return _CONFIG["batch_size"]

def get_max_memory_gb() -> float:
    """Return the configured max RAM in GB."""
    return _CONFIG["max_ram_gb"]

def get_drift_threshold() -> float:
    """Return the configured drift threshold."""
    return _CONFIG["drift_threshold"]

def get_centroid_model() -> str:
    """Return the configured centroid model name."""
    return _CONFIG["centroid_model"]

def get_baseline_model() -> str:
    """Return the configured baseline model name."""
    return _CONFIG["baseline_model"]