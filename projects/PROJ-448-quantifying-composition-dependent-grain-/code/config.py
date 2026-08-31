"""
Configuration constants for the project.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_FIGURES_DIR = DATA_DIR / "figures"
RESEARCH_DIR = PROJECT_ROOT / "research"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

# Data Manifest
DATA_MANIFEST_PATH = DATA_DIR / "data_manifest.json"

# Ground Truth Configuration
GENERATED_GROUND_TRUTH_FILENAME = "generated_ground_truth.csv"
SYNTHETIC_GROUND_TRUTH_CONFIG = RESEARCH_DIR / "synthetic_ground_truth.yaml"

# Random Seed for Reproducibility
RANDOM_SEED = 42

# Temperature Range (Kelvin)
TEMPERATURE_MIN = 500
TEMPERATURE_MAX = 1200
TEMPERATURE_STEP = 50

# Alloy Systems
BINARY_SYSTEMS = ["Fe-Cr", "Fe-Mo", "Fe-V", "Fe-W"]
TERNARY_SYSTEMS = ["Fe-Cr-Mo", "Fe-Cr-V", "Fe-Mo-V", "Fe-Cr-W", "Fe-Mo-W"]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
