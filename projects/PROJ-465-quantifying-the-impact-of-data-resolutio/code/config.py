"""
Configuration management for the project.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
TESTS_DIR = PROJECT_ROOT / "tests"

# Subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
DERIVED_DATA_DIR = DATA_DIR / "derived"
POSTERIORS_DIR = RESULTS_DIR / "posteriors"
METRICS_DIR = RESULTS_DIR / "metrics"

# Environment Variables
GWOSC_API_KEY = os.getenv("GWOSC_API_KEY", "")

def ensure_directories():
    """Create all required directories if they don't exist."""
    for d in [DATA_DIR, RAW_DATA_DIR, DERIVED_DATA_DIR, 
              RESULTS_DIR, POSTERIORS_DIR, METRICS_DIR, 
              FIGURES_DIR, CODE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
