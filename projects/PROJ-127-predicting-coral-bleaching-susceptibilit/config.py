import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_MODELS = PROJECT_ROOT / "data" / "models"
TESTS_DIR = PROJECT_ROOT / "tests"

# Paths
MODEL_PATH = DATA_MODELS
MODEL_OUTPUT = DATA_MODELS
UNIFIED_DATASET = DATA_PROCESSED / "reef_species_unified.csv"

# Data Sources (Placeholders - T031B should populate these or they are set dynamically)
# These are expected to be set by T031B or via environment variables
NOAA_URL = os.getenv("NOAA_URL", "https://example.com/noaa_sst_dhw")
CORAL_TRAIT_URL = os.getenv("CORAL_TRAIT_URL", "https://example.com/coral_traits")
UNEP_URL = os.getenv("UNEP_URL", "https://example.com/unep_reefs")
REEFBASE_URL = os.getenv("REEFBASE_URL", "https://example.com/reefbase_events")

# 2024 Raster URLs (Expected to be set by T031B)
RASTER_2024_SST = os.getenv("RASTER_2024_SST", "")
RASTER_2024_DHW = os.getenv("RASTER_2024_DHW", "")
RASTER_2024_THERMAL_TOLERANCE = os.getenv("RASTER_2024_THERMAL_TOLERANCE", "")

# Independent Reports
INDEPENDENT_BLEACHING_URL = os.getenv("INDEPENDENT_BLEACHING_URL", "")

# Configuration
RANDOM_SEED = 42
DATA_GAP_HALT = True
VIF_THRESHOLD = 5.0

# Output paths for artifacts
DATA_GAP_REPORT_PATH = PROJECT_ROOT / "data_gap_report.md"
RISK_MAP_PATH = DATA_MODELS / "bleaching_risk_map.tif"
THRESHOLD_REPORT_PATH = DATA_PROCESSED / "threshold_sensitivity.csv"
SENSITIVITY_REPORT_PATH = DATA_PROCESSED / "sensitivity_report.md"