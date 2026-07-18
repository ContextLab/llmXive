"""
Configuration management for the Prime Gap and Riemann Hypothesis study.

Defines global constants, paths, and the deterministic random seed management
required for reproducible research (Constitution Principle I).
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Global Constants
N_TARGET = 10**10  # Target prime generation limit (FR-001)
N_FALLBACK = 10**9 # Fallback limit if runtime exceeds SC-004
WINDOW_SIZE = 10**6 # Window size W for maximal gap analysis (FR-003)

# Deterministic Random Seed Management (T006)
# This constant ensures all random generators (numpy, python random)
# use the same seed for reproducibility across runs.
GLOBAL_SEED = 42

# Directory Paths
DIR_RAW = PROJECT_ROOT / "data" / "raw"
DIR_PROCESSED = PROJECT_ROOT / "data" / "processed"
DIR_RESULTS = PROJECT_ROOT / "data" / "results"
DIR_STATE = PROJECT_ROOT / "state" / "projects" / "PROJ-548-exploring-the-relationship-between-prime"
DIR_FIGURES = PROJECT_ROOT / "results"

# File Paths
STATE_FILE = DIR_STATE / "project.yaml"
PRIME_GAPS_FILE = DIR_PROCESSED / "primes_gaps.csv"
ZETA_ZEROS_FILE = DIR_PROCESSED / "zeta_zeros.csv"
KS_RESULTS_FILE = DIR_RESULTS / "correlation_results.json"
CDF_PLOT_FILE = DIR_RESULTS / "correlation_plot.png"
PERMUTATION_RESULTS_FILE = DIR_RESULTS / "permutation_test.json"
ROBUSTNESS_REPORT_FILE = DIR_RESULTS / "robustness_report.md"

def ensure_directories():
    """
    Create all required project directories if they do not exist.
    """
    for dir_path in [DIR_RAW, DIR_PROCESSED, DIR_RESULTS, DIR_STATE, DIR_FIGURES]:
        dir_path.mkdir(parents=True, exist_ok=True)

def get_global_seed():
    """
    Returns the global deterministic seed constant.
    Used by SeedManager to initialize RNGs.
    """
    return GLOBAL_SEED

def get_project_paths():
    """
    Returns a dictionary of all critical file paths.
    """
    return {
        "state": STATE_FILE,
        "primes_gaps": PRIME_GAPS_FILE,
        "zeta_zeros": ZETA_ZEROS_FILE,
        "ks_results": KS_RESULTS_FILE,
        "cdf_plot": CDF_PLOT_FILE,
        "permutation_results": PERMUTATION_RESULTS_FILE,
        "robustness_report": ROBUSTNESS_REPORT_FILE
    }
