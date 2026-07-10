"""
Configuration module for the Code Churn vs Technical Debt correlation study.

This module centralizes all parameter defaults, thresholds, and constants
required for reproducibility and sensitivity analysis.
"""
from pathlib import Path
from typing import Final, Dict, Any, List, Optional
import os

# Project Root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"

# Data Subdirectories
DATA_RAW: Final[Path] = DATA_DIR / "raw"
DATA_PROCESSED: Final[Path] = DATA_DIR / "processed"
DATA_RESULTS: Final[Path] = DATA_DIR / "results"
DATA_LOGS: Final[Path] = DATA_DIR / "logs"
FIGURES_DIR: Final[Path] = DATA_RESULTS / "plots"

# LOC Thresholds for Sensitivity Analysis (Plan Phase 4b)
LOC_THRESHOLDS: Final[List[int]] = [5, 10, 20]
DEFAULT_LOC_THRESHOLD: Final[int] = 10

# Repository Selection Limits
MAX_REPOS_TO_ANALYZE: Final[int] = 50
MIN_GITHUB_STARS: Final[int] = 500
MIN_REPO_AGE_YEARS: Final[int] = 2
MAX_CONCURRENT_CLONES: Final[int] = 4

# Tool Versions
RADON_VERSION: Final[str] = "0.0"  # Radon version string
SEMGREP_VERSION: Final[str] = "latest"
PYDRILLER_VERSION: Final[str] = "2.0.0"

# Analysis Parameters
VIF_THRESHOLD: Final[float] = 5.0
CORRELATION_MODERATE_THRESHOLD: Final[float] = 0.3
RANDOM_SEED: Final[int] = 42

# Timeouts (seconds)
CLONE_TIMEOUT: Final[int] = 600
ANALYSIS_TIMEOUT: Final[int] = 3600
PIPELINE_TIMEOUT: Final[int] = 7200

# File Paths (Relative to Data/Results)
UNIFIED_METRICS_FILE: Final[Path] = DATA_PROCESSED / "unified_metrics.csv"
REPOS_METADATA_FILE: Final[Path] = DATA_RAW / "repos_metadata.csv"
TOOL_VALIDATION_LOG_FILE: Final[Path] = DATA_LOGS / "tool_validation_log.csv"
CORRELATION_RESULTS_FILE: Final[Path] = DATA_RESULTS / "correlation_results.csv"
SENSITIVITY_ANALYSIS_FILE: Final[Path] = DATA_RESULTS / "sensitivity_analysis.csv"
META_ANALYSIS_RESULTS_FILE: Final[Path] = DATA_RESULTS / "meta_analysis_results.csv"
SUMMARY_REPORT_FILE: Final[Path] = DATA_RESULTS / "summary_report.txt"

# Supported Languages
SUPPORTED_LANGUAGES: Final[List[str]] = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust"
]

# File Extensions Mapping
FILE_EXTENSIONS: Final[Dict[str, List[str]]] = {
    "Python": [".py"],
    "Java": [".java"],
    "JavaScript": [".js", ".jsx", ".mjs"],
    "TypeScript": [".ts", ".tsx"],
    "Go": [".go"],
    "Rust": [".rs"]
}

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a dictionary summarizing the current configuration state.
    Useful for logging and reproducibility checks.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "loc_thresholds": LOC_THRESHOLDS,
        "default_loc_threshold": DEFAULT_LOC_THRESHOLD,
        "max_repos": MAX_REPOS_TO_ANALYZE,
        "min_stars": MIN_GITHUB_STARS,
        "min_age_years": MIN_REPO_AGE_YEARS,
        "radon_version": RADON_VERSION,
        "semgrep_version": SEMGREP_VERSION,
        "vif_threshold": VIF_THRESHOLD,
        "random_seed": RANDOM_SEED,
        "timeouts": {
            "clone": CLONE_TIMEOUT,
            "analysis": ANALYSIS_TIMEOUT,
            "pipeline": PIPELINE_TIMEOUT
        }
    }

def ensure_directories() -> None:
    """
    Creates all required project directories if they do not already exist.
    This should be called early in the pipeline initialization.
    """
    directories = [
        CODE_DIR, DATA_DIR, TESTS_DIR, CONTRACTS_DIR,
        DATA_RAW, DATA_PROCESSED, DATA_RESULTS, DATA_LOGS, FIGURES_DIR
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_env_override(key: str, default: str) -> str:
    """
    Retrieves an environment variable if set, otherwise returns the default.
    Used for optional overrides of configuration parameters.
    """
    return os.getenv(key, default)