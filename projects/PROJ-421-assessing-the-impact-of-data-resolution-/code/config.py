import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path("projects/PROJ-421-assessing-the-impact-of-data-resolution-")

# Directories
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Configuration
RESOLUTIONS = [30, 60, 120, 240, 480]
AGGREGATION_FACTORS = [1, 2, 4, 8, 16]
SEED = 42
N_PERMUTATIONS = 1000
N_SIMULATIONS = 1000
ALPHA = 0.05

# Paths
CALIBRATION_LAMBDA_PATH = DATA_RESULTS_DIR / "calibration_lambda.json"
POWER_RESULTS_PATH = DATA_RESULTS_DIR / "power_results.csv"
THRESHOLD_REPORT_PATH = DATA_RESULTS_DIR / "threshold_report.txt"
FINAL_REPORT_PATH = DATA_RESULTS_DIR / "final_report.md"

# Logging
LOG_LEVEL = "INFO"
