"""
Configuration module for llmXive research pipeline.

Contains pinned random seeds, path configurations, and threshold constants
required for reproducible research and consistent execution.
"""

import os
import random
from pathlib import Path
from typing import Final

# ============================================================================
# Random Seeds (Pinned for Reproducibility)
# ============================================================================
# All random number generators must be seeded with these values to ensure
# reproducible results across runs and environments.
RANDOM_SEED: Final[int] = 42
numpy_seed: Final[int] = 42
torch_seed: Final[int] = 42

# ============================================================================
# Threshold Constants
# ============================================================================
# These thresholds define the routing logic for prompt complexity:
# - LOW: < LOW_THRESHOLD
# - MEDIUM: LOW_THRESHOLD <= score <= HIGH_THRESHOLD
# - HIGH: > HIGH_THRESHOLD

LOW_THRESHOLD: Final[float] = 0.2
HIGH_THRESHOLD: Final[float] = 0.6

# ============================================================================
# Path Configuration
# ============================================================================
# All paths are relative to the project root.
# The project root is determined by locating the 'src' directory.

def _get_project_root() -> Path:
    """
    Determine the project root directory by traversing up from the current file.
    Assumes the standard structure: project_root/src/config.py
    """
    current_file = Path(__file__).resolve()
    src_dir = current_file.parent
    # Assume project root is the parent of src/
    project_root = src_dir.parent
    
    if not project_root.exists():
        raise RuntimeError(f"Project root not found at {project_root}")
    
    return project_root

PROJECT_ROOT: Final[Path] = _get_project_root()

# Raw data directory
DATA_RAW_DIR: Final[Path] = PROJECT_ROOT / "data" / "raw"

# Derived data directory
DATA_DERIVED_DIR: Final[Path] = PROJECT_ROOT / "data" / "derived"

# Figures/output directory
FIGURES_DIR: Final[Path] = PROJECT_ROOT / "figures"

# State directory for checksums and metadata
STATE_DIR: Final[Path] = PROJECT_ROOT / "state"

# Specific dataset paths
IA_BENCH_DIR: Final[Path] = DATA_RAW_DIR / "ia-bench"
WISE_VERIFIED_DIR: Final[Path] = DATA_RAW_DIR / "wise-verified"

# Output file paths
SCORING_RESULTS_PATH: Final[Path] = DATA_DERIVED_DIR / "scoring_results.csv"
ROUTING_DECISIONS_PATH: Final[Path] = DATA_DERIVED_DIR / "routing_decisions.csv"
FIDELITY_SCORES_PATH: Final[Path] = DATA_DERIVED_DIR / "fidelity_scores.csv"
REGRESSION_RESULTS_PATH: Final[Path] = DATA_DERIVED_DIR / "regression_results.json"
PILOT_CORRELATION_PATH: Final[Path] = DATA_DERIVED_DIR / "pilot_correlation.json"
MEMORY_PROFILE_LOG: Final[Path] = DATA_DERIVED_DIR / "memory_profile.log"

# Image output paths
IMAGES_BASELINE_FULL_SAMPLE: Final[Path] = DATA_DERIVED_DIR / "images" / "baseline" / "full_sample"
IMAGES_HYBRID_HIGH: Final[Path] = DATA_DERIVED_DIR / "images" / "hybrid" / "high"
IMAGES_BASELINE_HIGH: Final[Path] = DATA_DERIVED_DIR / "images" / "baseline" / "high"
IMAGES_PILOT_BASELINE: Final[Path] = DATA_DERIVED_DIR / "images" / "pilot" / "baseline"
IMAGES_PILOT_HYBRID: Final[Path] = DATA_DERIVED_DIR / "images" / "pilot" / "hybrid"

# References file
REFERENCES_PATH: Final[Path] = IA_BENCH_DIR / "references.jsonl"

# Checksums file
ARTIFACT_HASHES_PATH: Final[Path] = STATE_DIR / "artifact_hashes"

# ============================================================================
# Environment Variables (Optional Overrides)
# ============================================================================
# These can be overridden via environment variables for testing or deployment.

def get_env_path(var_name: str, default: Path) -> Path:
    """Get a path from an environment variable, falling back to default."""
    val = os.getenv(var_name)
    if val:
        return Path(val)
    return default

# Example: Override derived data directory if needed
# DATA_DERIVED_DIR = get_env_path("LLMXIVE_DERIVED_DATA", DATA_DERIVED_DIR)

# ============================================================================
# Validation
# ============================================================================
# Ensure critical directories exist (create if missing)

def ensure_directories() -> None:
    """Create all required directories if they do not exist."""
    dirs_to_create = [
        DATA_RAW_DIR,
        DATA_DERIVED_DIR,
        FIGURES_DIR,
        STATE_DIR,
        IA_BENCH_DIR,
        WISE_VERIFIED_DIR,
        IMAGES_BASELINE_FULL_SAMPLE,
        IMAGES_HYBRID_HIGH,
        IMAGES_BASELINE_HIGH,
        IMAGES_PILOT_BASELINE,
        IMAGES_PILOT_HYBRID,
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

# Execute directory creation on import
ensure_directories()