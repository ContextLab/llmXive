"""
Configuration management for the Prime Gap and Riemann Hypothesis analysis.

Defines global constants, default parameters, and file paths used throughout
the pipeline. Centralizes all "magic numbers" to ensure reproducibility and
easy parameter sweeps.

Key Parameters:
    N: Upper bound for prime generation (10^10).
    W: Window size for sliding window analysis (10^6).
    SEED: Base random seed for deterministic simulations.
"""
import os
from pathlib import Path
from typing import Final

# --- Project Roots ---
# Assumes this file is at: <project_root>/src/utils/config.py
# We navigate up two levels to find the project root.
_CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _CURRENT_DIR.parent.parent

# --- Core Constants ---
# Upper bound for prime generation (10^10)
N: Final[int] = 10**10

# Window size for sliding window analysis (10^6)
W: Final[int] = 10**6

# Base random seed for Monte Carlo and simulation tasks
SEED: Final[int] = 42

# --- Data Paths ---
# Raw data directory (for downloaded/external sources)
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# Processed data directory (for generated primes, gaps, zeros)
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Null/Synthetic data directory (for Cramer model comparisons)
DATA_NULL = PROJECT_ROOT / "data" / "null"

# Results directory (for analysis outputs, plots, JSON)
RESULTS = PROJECT_ROOT / "results"

# State directory (for checkpoints, logs, state.yaml)
STATE = PROJECT_ROOT / "state"

# --- File Specific Paths ---
# Output path for generated prime gaps
PRIMES_GAPS_CSV = DATA_PROCESSED / "primes_gaps.csv"

# Output path for ingested Zeta zeros
ZETA_ZEROS_CSV = DATA_PROCESSED / "zeta_zeros.csv"

# Output path for Cramer model null sample
CRAMER_SAMPLE_CSV = DATA_NULL / "cramer_sample.csv"

# Output path for correlation results (JSON)
CORRELATION_RESULTS_JSON = RESULTS / "correlation_results.json"

# Output path for correlation plot (PNG)
CORRELATION_PLOT_PNG = RESULTS / "correlation_plot.png"

# Output path for robustness report
ROBUSTNESS_REPORT_MD = RESULTS / "robustness_report.md"

# State file for pipeline tracking
STATE_YAML = STATE / "state.yaml"

# --- Logging Configuration ---
LOGS_DIR = STATE / "logs"
LOG_FILE = LOGS_DIR / "pipeline.log"

# --- Analysis Parameters ---
# Number of Monte Carlo iterations for null distribution
MC_ITERATIONS: Final[int] = 1000

# Window sizes for robustness sweep (US3)
ROBUSTNESS_WINDOWS: Final[list[int]] = [10**5, 10**6, 2 * 10**6]

def ensure_directories() -> None:
    """
    Creates all required project directories if they do not exist.
    This should be called during initialization or before data generation.
    """
    dirs = [
        DATA_RAW,
        DATA_PROCESSED,
        DATA_NULL,
        RESULTS,
        STATE,
        LOGS_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Ensure directories exist upon import if running as a module
# (Optional safety, but explicit calls in scripts are preferred for control)
if __name__ == "__main__":
    ensure_directories()
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Raw: {DATA_RAW}")
    print(f"Data Processed: {DATA_PROCESSED}")
    print(f"Results: {RESULTS}")
    print(f"N (Prime Limit): {N}")
    print(f"W (Window Size): {W}")
    print(f"Seed: {SEED}")