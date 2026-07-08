"""
Configuration module for the Code Complexity Bug Prediction pipeline.

Defines environment variables, fixed random seeds, and memory limits
required for reproducible and resource-constrained execution.
"""
import os
from pathlib import Path
from typing import Optional

# --- Environment Variables ---
# Path to the Defects4J installation directory.
# If not set, defaults to the standard installation path or raises an error if needed.
DEFECTS4J_PATH: str = os.environ.get("DEFECTS4J_PATH", "/opt/defects4j")

# Path to the PMD CLI tool installation.
PMD_PATH: str = os.environ.get("PMD_PATH", "/usr/bin/pmd")

# --- Random Seeds ---
# Fixed seed for reproducibility across the entire pipeline.
# Used by numpy, random, and scikit-learn.
RANDOM_SEED: int = 42

# --- Resource Limits ---
# Maximum RAM usage in GB for dynamic subset validation (T004, T013).
# The ingestion process will stop adding projects when this limit is approached.
MEMORY_LIMIT_GB: int = 7

# Maximum number of CPU cores to utilize for parallel metric extraction.
# Set to None to use all available cores, or an integer.
MAX_WORKERS: Optional[int] = None

# --- Project Paths ---
# Base directory for the project root (where code/, data/, etc. reside).
# Resolves relative to the script location if run as a module, or current dir.
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
if not (PROJECT_ROOT / "code").exists():
    # Fallback if running from a different context
    PROJECT_ROOT = Path.cwd()

# Data directories
DATA_RAW_DIR: Path = PROJECT_ROOT / "code" / "data" / "raw"
DATA_PROCESSED_DIR: Path = PROJECT_ROOT / "code" / "data" / "processed"
DATA_RESULTS_DIR: Path = PROJECT_ROOT / "code" / "data" / "results"

# Ensure directories exist (optional, can be moved to a setup task if preferred)
# For config, we just define them, but ensuring they exist helps downstream scripts.
# We do not force creation here to keep config pure, but we define the paths.

# --- Validation Helpers ---
def validate_defects4j_path() -> bool:
    """Checks if the configured Defects4J path exists."""
    return Path(DEFECTS4J_PATH).exists()

def validate_pmd_path() -> bool:
    """Checks if the configured PMD path exists."""
    return Path(PMD_PATH).exists()

def get_memory_limit_bytes() -> int:
    """Returns the memory limit in bytes."""
    return MEMORY_LIMIT_GB * 1024 * 1024 * 1024

# Export public API
__all__ = [
    "DEFECTS4J_PATH",
    "PMD_PATH",
    "RANDOM_SEED",
    "MEMORY_LIMIT_GB",
    "MAX_WORKERS",
    "PROJECT_ROOT",
    "DATA_RAW_DIR",
    "DATA_PROCESSED_DIR",
    "DATA_RESULTS_DIR",
    "validate_defects4j_path",
    "validate_pmd_path",
    "get_memory_limit_bytes",
]