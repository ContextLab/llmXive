"""
Global configuration for the Visual Complexity & Cognitive Load project.

This module defines the global random seed for reproducibility and
absolute/relative path definitions for the project structure.
"""
import os
from pathlib import Path
from typing import Final

# --- Reproducibility ---
# Global random seed used across numpy, python random, and torch (if used)
# to ensure deterministic results for experiments and metric extraction.
GLOBAL_SEED: Final[int] = 42

# --- Project Paths ---
# Resolve the project root based on the location of this config file.
# Structure: code/src/config.py -> project root is two levels up.
_CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT: Final[Path] = _CURRENT_FILE.parent.parent.parent

# --- Directory Definitions ---
# Code directories
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
SRC_DIR: Final[Path] = PROJECT_ROOT / "code" / "src"
LIB_DIR: Final[Path] = SRC_DIR / "lib"
METRICS_DIR: Final[Path] = SRC_DIR / "metrics"
EXPERIMENT_DIR: Final[Path] = SRC_DIR / "experiment"
ANALYSIS_DIR: Final[Path] = SRC_DIR / "analysis"

# Test directories
TESTS_DIR: Final[Path] = PROJECT_ROOT / "code" / "tests"

# Data directories
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
DATA_RAW_DIR: Final[Path] = DATA_DIR / "raw"
DATA_STIMULI_DIR: Final[Path] = DATA_DIR / "stimuli"
DATA_STIMULI_RAW_DIR: Final[Path] = DATA_STIMULI_DIR / "raw"
DATA_STIMULI_NEUTRAL_DIR: Final[Path] = DATA_STIMULI_DIR / "neutral"
DATA_PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
DATA_MEASUREMENTS_DIR: Final[Path] = DATA_DIR / "measurements"
DATA_MEASUREMENTS_RAW_DIR: Final[Path] = DATA_MEASUREMENTS_DIR / "raw"
DATA_DERIVED_DIR: Final[Path] = DATA_DIR / "derived"
DATA_DERIVED_VALIDATION_ONLY_DIR: Final[Path] = DATA_DERIVED_DIR / "validation_only"

# Output specific files
METRICS_CSV_PATH: Final[Path] = DATA_PROCESSED_DIR / "metrics.csv"
HUMAN_RATINGS_CSV_PATH: Final[Path] = DATA_MEASUREMENTS_DIR / "human_ratings.csv"
PARTICIPANT_SESSIONS_CSV_PATH: Final[Path] = DATA_MEASUREMENTS_RAW_DIR / "participant_sessions.csv"
CURATED_CLIPS_CSV_PATH: Final[Path] = DATA_PROCESSED_DIR / "curated_clips.csv"
CLIP_DIFFICULTY_CSV_PATH: Final[Path] = DATA_PROCESSED_DIR / "clip_difficulty.csv"
ANALYSIS_INPUT_CSV_PATH: Final[Path] = DATA_PROCESSED_DIR / "analysis_input.csv"
STABILITY_REPORT_CSV_PATH: Final[Path] = DATA_DERIVED_DIR / "stability_report.csv"
FWER_VALIDATION_REPORT_PATH: Final[Path] = DATA_DERIVED_DIR / "fwer_validation_report.md"
PILOT_VALIDATION_REPORT_PATH: Final[Path] = DATA_DERIVED_DIR / "pilot_validation_report.md"
RT_MEASUREMENTS_JSON_PATH: Final[Path] = DATA_DERIVED_DIR / "rt_measurements.json"
PERFORMANCE_LOG_PATH: Final[Path] = DATA_DERIVED_DIR / "performance_log.txt"

# Logs and State
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
STATE_DIR: Final[Path] = PROJECT_ROOT / "state"
ARTIFACT_HASHES_DIR: Final[Path] = STATE_DIR / "artifact_hashes"

# Configuration files
REQUIREMENTS_PATH: Final[Path] = PROJECT_ROOT / "requirements.txt"
PYPROJECT_PATH: Final[Path] = PROJECT_ROOT / "pyproject.toml"

# --- Helper Functions ---
def ensure_directories_exist() -> None:
    """
    Creates all defined directories if they do not already exist.
    This should be called during initialization or setup tasks.
    """
    all_dirs = [
        CODE_DIR, SRC_DIR, LIB_DIR, METRICS_DIR, EXPERIMENT_DIR, ANALYSIS_DIR,
        TESTS_DIR,
        DATA_DIR, DATA_RAW_DIR, DATA_STIMULI_DIR, DATA_STIMULI_RAW_DIR, 
        DATA_STIMULI_NEUTRAL_DIR, DATA_PROCESSED_DIR, DATA_MEASUREMENTS_DIR, 
        DATA_MEASUREMENTS_RAW_DIR, DATA_DERIVED_DIR, DATA_DERIVED_VALIDATION_ONLY_DIR,
        LOGS_DIR, STATE_DIR, ARTIFACT_HASHES_DIR
    ]
    for dir_path in all_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

def get_relative_path(path: Path) -> Path:
    """
    Returns the path relative to the project root.
    """
    try:
        return path.relative_to(PROJECT_ROOT)
    except ValueError:
        return path
