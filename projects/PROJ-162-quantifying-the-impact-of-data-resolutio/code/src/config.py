"""
Global configuration constants and utility functions for the llmXive project.

This module defines:
- Global random seeds for reproducibility
- Project directory paths
- Target resolution frequencies (Hz)
- Contract schema paths
- Utility functions for path resolution and directory management
"""

import os
from pathlib import Path
from typing import Final, List, Optional

# =============================================================================
# Global Seeds for Reproducibility
# =============================================================================
RANDOM_SEED: Final[int] = 42
NUMPY_SEED: Final[int] = 42
TORCH_SEED: Final[int] = 42  # If PyTorch is used in future extensions

# =============================================================================
# Target Resolution Frequencies (Hz)
# =============================================================================
# These are the sampling rates at which waveforms will be analyzed
RESOLUTION_TARGETS: Final[List[int]] = [4096, 2048, 1024, 512, 256]

# The base (highest) resolution used for waveform generation
BASE_RESOLUTION: Final[int] = 4096

# =============================================================================
# Project Paths
# =============================================================================
# Determine the project root (parent of the 'code' directory)
# This assumes the project structure: code/src/, code/tests/, etc.
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
_CODE_ROOT: Final[Path] = _PROJECT_ROOT / "code"

# Directory paths
DATA_DIR: Final[Path] = _PROJECT_ROOT / "data"
DATA_RAW_DIR: Final[Path] = DATA_DIR / "raw"
DATA_PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
DATA_FIGURES_DIR: Final[Path] = DATA_DIR / "figures"

CONTRACTS_DIR: Final[Path] = _PROJECT_ROOT / "contracts"
SPECS_DIR: Final[Path] = _PROJECT_ROOT / "specs" / "001-quantifying-the-impact-of-data-resolutio"

OUTPUT_DIR: Final[Path] = DATA_PROCESSED_DIR
FIGURES_DIR: Final[Path] = DATA_FIGURES_DIR

# =============================================================================
# Analysis Parameters
# =============================================================================
# Detection threshold for re-weighted SNR
DETECTION_THRESHOLD: Final[float] = 8.0

# Minimum separation interval for injection time offsets (seconds)
MIN_INJECTION_SEPARATION: Final[float] = 0.5

# Power analysis defaults
POWER_ANALYSIS_PILOT_N: Final[int] = 20
POWER_ANALYSIS_TARGET_POWER: Final[float] = 0.8
POWER_ANALYSIS_MAX_N: Final[int] = 200
POWER_ANALYSIS_SIGMA_REL: Final[float] = 0.05

# Statistical test parameters
CHI_SQUARE_DF: Final[int] = 16  # Number of frequency bins for chi-squared test

# =============================================================================
# File Paths for Contracts
# =============================================================================
INJECTION_SCHEMA_PATH: Final[Path] = CONTRACTS_DIR / "injection.schema.yaml"
DETECTION_METRIC_SCHEMA_PATH: Final[Path] = CONTRACTS_DIR / "detection_metric.schema.yaml"

# =============================================================================
# Utility Functions
# =============================================================================

def get_contract_path(schema_name: str) -> Path:
    """
    Resolve the full path to a contract schema file.
    
    Args:
        schema_name: Name of the schema file (e.g., 'injection.schema.yaml')
        
    Returns:
        Absolute Path to the schema file
        
    Raises:
        FileNotFoundError: If the schema file does not exist
    """
    path = CONTRACTS_DIR / schema_name
    if not path.exists():
        raise FileNotFoundError(f"Contract schema not found: {path}")
    return path

def ensure_directories() -> None:
    """
    Create all required project directories if they do not exist.
    
    This function ensures that the following directories are present:
    - data/
    - data/raw/
    - data/processed/
    - data/figures/
    - contracts/
    - specs/
    
    Note: This is idempotent and safe to call multiple times.
    """
    directories = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_FIGURES_DIR,
        CONTRACTS_DIR,
        SPECS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_data_path(filename: str, subdirectory: Optional[str] = None) -> Path:
    """
    Construct a full path within the data directory.
    
    Args:
        filename: Name of the file
        subdirectory: Optional subdirectory within data/ (e.g., 'raw', 'processed')
        
    Returns:
        Absolute Path to the file
    """
    if subdirectory:
        return DATA_DIR / subdirectory / filename
    return DATA_DIR / filename

def get_processed_path(filename: str) -> Path:
    """
    Construct a full path within the processed data directory.
    
    Args:
        filename: Name of the file
        
    Returns:
        Absolute Path to the file
    """
    return DATA_PROCESSED_DIR / filename

def get_figure_path(filename: str) -> Path:
    """
    Construct a full path within the figures directory.
    
    Args:
        filename: Name of the figure file
        
    Returns:
        Absolute Path to the file
    """
    return FIGURES_DIR / filename

# =============================================================================
# Validation
# =============================================================================
def validate_config() -> None:
    """
    Validate that all critical configuration paths and values are set correctly.
    
    Raises:
        ValueError: If any critical configuration is invalid
    """
    if BASE_RESOLUTION not in RESOLUTION_TARGETS:
        raise ValueError(f"Base resolution {BASE_RESOLUTION} must be in RESOLUTION_TARGETS")
    
    if len(RESOLUTION_TARGETS) == 0:
        raise ValueError("RESOLUTION_TARGETS cannot be empty")
    
    if RESOLUTION_TARGETS != sorted(RESOLUTION_TARGETS, reverse=True):
        raise ValueError("RESOLUTION_TARGETS should be sorted in descending order")
    
    # Check that required directories can be created
    ensure_directories()
    
    # Check that contract schemas exist (if they are expected to be present)
    # Note: We don't raise an error if they don't exist yet, as they may be created later
    # But we log a warning if they are missing
    if not INJECTION_SCHEMA_PATH.exists():
        print(f"Warning: Injection schema not found at {INJECTION_SCHEMA_PATH}")
    
    if not DETECTION_METRIC_SCHEMA_PATH.exists():
        print(f"Warning: Detection metric schema not found at {DETECTION_METRIC_SCHEMA_PATH}")

# =============================================================================
# Initialization
# =============================================================================
if __name__ == "__main__":
    # Run validation when executed directly
    validate_config()
    print("Configuration validated successfully.")
    print(f"Project root: {_PROJECT_ROOT}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Resolution targets: {RESOLUTION_TARGETS}")
    print(f"Random seed: {RANDOM_SEED}")
