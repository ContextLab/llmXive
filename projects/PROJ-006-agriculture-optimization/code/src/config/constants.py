import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_LOGS_DIR = PROJECT_ROOT / "data" / "logs"

# Configuration Constants
RANDOM_SEED = 42
BUFFER_SIZE_KM = 1.0
GRID_RESOLUTION_KM = 0.1
CLOUD_COVER_THRESHOLD = 0.9

# API Tokens (must be set in environment)
WB_LSMS_TOKEN = os.environ.get("WB_LSMS_TOKEN", "")
COPERNICUS_USER = os.environ.get("COPERNICUS_USER", "")
COPERNICUS_PASSWORD = os.environ.get("COPERNICUS_PASSWORD", "")

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
