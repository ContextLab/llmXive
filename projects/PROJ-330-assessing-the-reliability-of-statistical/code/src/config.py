"""
Configuration module for the genomic statistical reliability analysis pipeline.

This module centralizes all runtime constants, random seeds, file paths,
and execution thresholds to ensure reproducibility and consistent behavior
across the entire pipeline.
"""

import os
from pathlib import Path
from typing import Final

# ============================================================================
# Project Root and Directory Constants
# ============================================================================

# Determine the project root (parent of the 'code' directory)
# Assumes this file is at code/src/config.py
_CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT: Final[Path] = _CURRENT_FILE.parent.parent.parent

# Standardized directory paths relative to PROJECT_ROOT
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
SCRIPTS_DIR: Final[Path] = CODE_DIR / "scripts"
SRC_DIR: Final[Path] = CODE_DIR / "src"
TESTS_DIR: Final[Path] = CODE_DIR / "tests"
SPEC_DIR: Final[Path] = PROJECT_ROOT / "specs" / "001-assess-significance-reliability"
FIGURES_DIR: Final[Path] = DATA_DIR / "figures"
ARTIFACTS_DIR: Final[Path] = DATA_DIR / "artifacts"

# Ensure directories exist (lazy initialization check)
def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    for directory in [DATA_DIR, SCRIPTS_DIR, SRC_DIR, TESTS_DIR, FIGURES_DIR, ARTIFACTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Reproducibility: Random Seeds
# ============================================================================

# Global random seed for numpy, python random, and torch (if used)
# Setting this ensures reproducible results for stratification and permutations
RANDOM_SEED: Final[int] = 42

# ============================================================================
# Execution Thresholds and Limits
# ============================================================================

# Maximum runtime for the entire analysis pipeline (in seconds)
# 6 hours = 6 * 60 * 60 = 21600 seconds
MAX_RUNTIME_SECONDS: Final[int] = 6 * 60 * 60

# Minimum number of permutations required for the null model analysis
# Ensures statistical power for p-value estimation even if time runs out
MIN_PERMUTATIONS: Final[int] = 100

# Maximum number of permutations (soft cap, may be exceeded if time allows)
MAX_PERMUTATIONS: Final[int] = 10000

# Minimum sample size required for a dataset to be included in the analysis
# Datasets with fewer samples will be skipped with a warning
MIN_SAMPLES: Final[int] = 20

# Minimum number of genes required across all categories for valid analysis
MIN_GENES: Final[int] = 5

# ============================================================================
# File Paths and Manifests
# ============================================================================

# Path to the data manifest file (JSON/YAML) listing available datasets
DATA_MANIFEST_PATH: Final[Path] = DATA_DIR / "manifest.json"

# Path to the state tracking file (stores artifact hashes and run metadata)
STATE_FILE_PATH: Final[Path] = PROJECT_ROOT / "state.yaml"

# Path to the requirements file
REQUIREMENTS_PATH: Final[Path] = PROJECT_ROOT / "requirements.txt"

# Path to the R script for differential expression analysis
R_DE_SCRIPT_PATH: Final[Path] = SCRIPTS_DIR / "run_r_script.R"

# ============================================================================
# Analysis Parameters
# ============================================================================

# Log2 fold-change threshold for significance (used in filtering if needed)
LOG2FC_THRESHOLD: Final[float] = 1.0

# P-value threshold for significance (unadjusted)
PVALUE_THRESHOLD: Final[float] = 0.05

# Number of stratified subsets for stability analysis (US1)
NUM_SUBSETS: Final[int] = 5

# ============================================================================
# Logging and Verbosity
# ============================================================================

# Default log level for the pipeline
DEFAULT_LOG_LEVEL: Final[str] = "INFO"

# ============================================================================
# Environment Overrides
# ============================================================================

# Allow overriding random seed via environment variable for testing
if "RANDOM_SEED" in os.environ:
    try:
        RANDOM_SEED = int(os.environ["RANDOM_SEED"])
    except ValueError:
        pass  # Fall back to default if invalid

# Allow overriding max runtime via environment variable
if "MAX_RUNTIME_SECONDS" in os.environ:
    try:
        MAX_RUNTIME_SECONDS = int(os.environ["MAX_RUNTIME_SECONDS"])
    except ValueError:
        pass