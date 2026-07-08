"""
Configuration module for the Coral Bleaching Susceptibility project.
Contains paths, random seeds, thresholds, and flags.
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_MODELS_DIR = PROJECT_ROOT / "data" / "models"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Random Seeds
RANDOM_SEED = 42

# Thresholds
VIF_THRESHOLD = 5.0
DATA_GAP_THRESHOLD = 0.1  # Fraction of missing data allowed
BLEACHING_THRESHOLD = 0.5 # Probability threshold for high risk

# Flags
DATA_GAP_HALT = True

# URLs for data sources (to be populated with real URLs)
NOAA_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap"
CORAL_TRAIT_URL = "https://coraltraitdatabase.org/api"
UNEP_REEFS_URL = "https://data.unep-wcmc.org/datasets/reef"
REEFBASE_URL = "https://www.reefbase.org/api"
RASTER_2024_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap"
INDEPENDENT_BLEACHING_URL = "https://data.reefbase.org/bleaching_reports"
