"""
Configuration management for the llmXive science pipeline.
Centralizes paths, random seeds, and threshold constants.
"""
import os
from pathlib import Path
from typing import Final

# Project constants
PROJECT_NAME: Final[str] = "PROJ-065-assessing-the-generalizability-of-statis"
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent
PROJECT_PATH: Final[Path] = PROJECT_ROOT / PROJECT_NAME

# Random seed for reproducibility
RANDOM_SEED: Final[int] = 42

# Iteration limits
MAX_ITERATIONS: Final[int] = 1000
ALTERNATIVE_ITERATIONS: Final[int] = 1000

# Time limits (in hours)
TIMEOUT_HOURS: Final[int] = 6

# Threshold constants
P_VALUE_THRESHOLD: Final[float] = 0.05
STABILITY_THRESHOLD: Final[float] = 0.80

# OSF API configuration
OSF_API_BASE_URL: Final[str] = "https://api.osf.io/v2"
OSF_MAX_RETRIES: Final[int] = 5
OSF_BACKOFF_BASE: Final[int] = 2
OSF_BACKOFF_FACTOR: Final[int] = 2

# File paths
DATA_RAW_DIR: Final[Path] = PROJECT_PATH / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = PROJECT_PATH / "data" / "processed"
OUTPUTS_DIR: Final[Path] = PROJECT_PATH / "outputs"
OUTPUTS_FIGURES_DIR: Final[Path] = OUTPUTS_DIR / "figures"
OUTPUTS_REPORTS_DIR: Final[Path] = OUTPUTS_DIR / "reports"
CODE_DIR: Final[Path] = PROJECT_PATH / "code"
TESTS_DIR: Final[Path] = PROJECT_PATH / "tests"

# Output files
BASELINE_METRICS_FILE: Final[Path] = DATA_PROCESSED_DIR / "baseline_metrics.csv"
SUMMARY_STATS_FILE: Final[Path] = DATA_PROCESSED_DIR / "summary_stats.csv"
SENSITIVITY_RESULTS_FILE: Final[Path] = DATA_PROCESSED_DIR / "sensitivity_results.csv"

def ensure_config_dirs() -> None:
    """
    Ensure all required configuration directories exist.
    This function is a wrapper to guarantee directory structure is initialized.
    """
    import os
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        OUTPUTS_DIR,
        OUTPUTS_FIGURES_DIR,
        OUTPUTS_REPORTS_DIR,
        CODE_DIR,
        TESTS_DIR,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        # Create .gitkeep to ensure directory tracking
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

if __name__ == "__main__":
    print(f"Project Path: {PROJECT_PATH}")
    print(f"Data Raw: {DATA_RAW_DIR}")
    print(f"Data Processed: {DATA_PROCESSED_DIR}")
    print(f"Outputs: {OUTPUTS_DIR}")
    print(f"Outputs Figures: {OUTPUTS_FIGURES_DIR}")
    print(f"Outputs Reports: {OUTPUTS_REPORTS_DIR}")
    print("Ensuring directories...")
    ensure_config_dirs()
    print("Done.")
