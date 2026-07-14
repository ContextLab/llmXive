"""
Configuration module for the Statistical Analysis of Publicly Available Chess Game Data project.

This module defines:
- Random seeds for reproducibility
- File path constants for project directories
- Lichess dataset URL constants
"""
import os
from pathlib import Path
from typing import Optional

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ==============================================================================
# Random Seeds
# ==============================================================================
RANDOM_SEED: int = 42
NP_RANDOM_SEED: int = 42
torch_seed: Optional[int] = None  # Only if torch is added later

# ==============================================================================
# Directory Paths
# ==============================================================================
DATA_RAW_DIR: Path = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Path = _PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR: Path = _PROJECT_ROOT / "data" / "results"
SPEC_DIR: Path = _PROJECT_ROOT / "specs"
CONTRACTS_DIR: Path = SPEC_DIR / "contracts"
FIGURES_DIR: Path = DATA_RESULTS_DIR / "figures"

# Ensure directories exist (lazy initialization helper)
def _ensure_dirs():
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR, CONTRACTS_DIR, FIGURES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# Lichess Dataset URLs
# ==============================================================================
# HuggingFace dataset repository containing Lichess games
LICHES_HF_DATASET_ID: str = "lichess/lichess-games"
LICHES_HF_CONFIG: str = "2023"  # Example config, adjust based on actual dataset version
LICHES_HF_SPLIT: str = "train"

# Direct download URL for a specific PGN file (if available)
# Using a representative sample URL from Lichess public exports
LICHES_EXPORT_BASE_URL: str = "https://database.lichess.org"
LICHES_EXPORT_FILE_TEMPLATE: str = "lichess_db_standard_rated_{}.pgn.zst"

# Example specific year/month for testing (2023-01)
LICHES_SAMPLE_URL: str = f"{LICHES_EXPORT_BASE_URL}/lichess_db_standard_rated_2023-01.pgn.zst"

# ==============================================================================
# Helper Functions
# ==============================================================================
def get_contract_path(contract_name: str) -> Path:
    """
    Returns the full path to a contract schema file.

    Args:
        contract_name: Name of the schema file (e.g., 'game_record.schema.yaml')

    Returns:
        Path object pointing to the schema file.
    """
    return CONTRACTS_DIR / contract_name

def get_data_path(sub_dir: str, filename: str) -> Path:
    """
    Returns the full path to a data file within a specified subdirectory.

    Args:
        sub_dir: Subdirectory name ('raw', 'processed', 'results')
        filename: Name of the file

    Returns:
        Path object pointing to the data file.
    """
    base_map = {
        "raw": DATA_RAW_DIR,
        "processed": DATA_PROCESSED_DIR,
        "results": DATA_RESULTS_DIR
    }
    if sub_dir not in base_map:
        raise ValueError(f"Unknown sub_dir: {sub_dir}. Must be one of {list(base_map.keys())}")
    return base_map[sub_dir] / filename

def get_figures_path(filename: str) -> Path:
    """
    Returns the full path for a figure file.

    Args:
        filename: Name of the figure file.

    Returns:
        Path object pointing to the figure file.
    """
    return FIGURES_DIR / filename

# Initialize directories on module import if needed
try:
    _ensure_dirs()
except PermissionError:
    # In read-only environments, this might fail, which is acceptable for config loading
    pass