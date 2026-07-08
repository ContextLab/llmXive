"""
Configuration module for the llmXive research pipeline.
Defines paths, random seeds, and threshold constants.
"""
import os
from pathlib import Path
from typing import Final

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Directory Paths
DATA_RAW_DIR: Final[Path] = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR: Final[Path] = PROJECT_ROOT / "outputs"
OUTPUTS_FIGURES_DIR: Final[Path] = OUTPUTS_DIR / "figures"
OUTPUTS_REPORTS_DIR: Final[Path] = OUTPUTS_DIR / "reports"
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"
SPECS_DIR: Final[Path] = PROJECT_ROOT / "specs"

# Random Seeds
RANDOM_SEED: Final[int] = 42

# Iteration Thresholds
MAX_ITERATIONS: Final[int] = 1000
ALTERNATIVE_ITERATIONS: Final[int] = 1000

# Timeouts and Limits
TIMEOUT_HOURS: Final[int] = 6
MAX_RUNTIME_SECONDS: Final[int] = TIMEOUT_HOURS * 3600

# Statistical Thresholds
ALPHA_THRESHOLD: Final[float] = 0.05
SIGIFICANCE_THRESHOLDS: Final[list[float]] = [0.01, 0.05, 0.10]

# OSF Configuration
OSF_API_BASE_URL: Final[str] = "https://api.osf.io/v2"
OSF_MAX_RETRIES: Final[int] = 5
OSF_BACKOFF_FACTOR: Final[float] = 2.0

# Memory Constraints (in GB)
MAX_MEMORY_GB: Final[float] = 6.0

# Subsampling Limits
MAX_SUBSAMPLE_SIZE: Final[int] = 2000

# Ensure directories exist on import (optional safety check)
def ensure_config_dirs() -> None:
    """Create configuration directories if they do not exist."""
    for directory in [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        OUTPUTS_DIR,
        OUTPUTS_FIGURES_DIR,
        OUTPUTS_REPORTS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

# Execute directory check on module load
if not os.getenv("SKIP_DIR_CHECK"):
    ensure_config_dirs()
