"""
Configuration module for the Visual Complexity Impact project.

Defines global constants for random seeds, directory paths, and file locations.
"""
import os
from pathlib import Path
from typing import Final

# Global random seed for reproducibility
GLOBAL_SEED: Final[int] = 42

# Project root directory (assumed to be the parent of 'code')
# This script is located at code/src/config.py, so we go up two levels
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent

# Base data directory
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"

# Specific data subdirectories
DATA_RAW_DIR: Final[Path] = DATA_DIR / "raw"
DATA_PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
DATA_STIMULI_DIR: Final[Path] = DATA_DIR / "stimuli"
DATA_STIMULI_RAW_DIR: Final[Path] = DATA_STIMULI_DIR / "raw"
DATA_STIMULI_NEUTRAL_DIR: Final[Path] = DATA_STIMULI_DIR / "neutral"
DATA_MEASUREMENTS_DIR: Final[Path] = DATA_DIR / "measurements"
DATA_DERIVED_DIR: Final[Path] = DATA_DIR / "derived"
DATA_METADATA_DIR: Final[Path] = DATA_DIR / "metadata"

# Output file paths
METRICS_CSV_PATH: Final[Path] = DATA_PROCESSED_DIR / "metrics.csv"
HUMAN_RATINGS_CSV_PATH: Final[Path] = DATA_MEASUREMENTS_DIR / "human_ratings.csv"
PARTICIPANT_SESSIONS_CSV_PATH: Final[Path] = DATA_MEASUREMENTS_DIR / "raw" / "participant_sessions.csv"
CLIP_DIFFICULTY_CSV_PATH: Final[Path] = DATA_PROCESSED_DIR / "clip_difficulty.csv"
COUNTERBALANCE_ORDER_PATH: Final[Path] = DATA_PROCESSED_DIR / "counterbalance_order.json"
DATASET_MANIFEST_PATH: Final[Path] = DATA_METADATA_DIR / "dataset_manifest.json"
CLIP_MANIFEST_PATH: Final[Path] = DATA_METADATA_DIR / "clip_manifest.json"
CURATED_MANIFEST_PATH: Final[Path] = DATA_METADATA_DIR / "curated_manifest.json"
COHORT_PATH: Final[Path] = DATA_MEASUREMENTS_DIR / "cohort.json"
RT_MEASUREMENTS_PATH: Final[Path] = DATA_DERIVED_DIR / "rt_measurements.json"
STABILITY_REPORT_PATH: Final[Path] = DATA_DERIVED_DIR / "stability_report.csv"
STABILITY_CONCLUSION_PATH: Final[Path] = DATA_DERIVED_DIR / "stability_conclusion.txt"
FWER_VALIDATION_REPORT_PATH: Final[Path] = DATA_DERIVED_DIR / "fwer_validation_report.md"
PILOT_VALIDATION_REPORT_PATH: Final[Path] = DATA_DERIVED_DIR / "pilot_validation_report.md"
COMPLEXITY_TLX_CORRELATION_PATH: Final[Path] = DATA_DERIVED_DIR / "complexity_tlx_correlation.csv"
RT_DIFF_PATH: Final[Path] = DATA_DERIVED_DIR / "rt_diff.csv"
PERFORMANCE_LOG_PATH: Final[Path] = DATA_DERIVED_DIR / "performance_log.txt"

# Log directory and files
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
PILOT_REVIEW_FLAG_LOG: Final[Path] = LOGS_DIR / "pilot_review_flag.log"
VALIDATE_STIMULI_LOG: Final[Path] = LOGS_DIR / "validate_stimuli.log"

# State directory
STATE_DIR: Final[Path] = PROJECT_ROOT / "state"
ARTIFACT_HASHES_DIR: Final[Path] = STATE_DIR / "artifact_hashes"

# Documentation directory
DOCS_DIR: Final[Path] = PROJECT_ROOT / "docs"

# Contracts directory
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"

# Figures directory
FIGURES_DIR: Final[Path] = PROJECT_ROOT / "figures"

def ensure_directories_exist() -> None:
    """Create all defined directories if they do not exist."""
    all_dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_STIMULI_DIR,
        DATA_STIMULI_RAW_DIR,
        DATA_STIMULI_NEUTRAL_DIR,
        DATA_MEASUREMENTS_DIR,
        DATA_DERIVED_DIR,
        DATA_METADATA_DIR,
        LOGS_DIR,
        STATE_DIR,
        ARTIFACT_HASHES_DIR,
        DOCS_DIR,
        CONTRACTS_DIR,
        FIGURES_DIR,
        DATA_MEASUREMENTS_DIR / "raw",
    ]
    for directory in all_dirs:
        directory.mkdir(parents=True, exist_ok=True)

def get_relative_path(path: Path) -> str:
    """Convert an absolute path to a path relative to the project root."""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        # If path is not under project root, return absolute path
        return str(path)
