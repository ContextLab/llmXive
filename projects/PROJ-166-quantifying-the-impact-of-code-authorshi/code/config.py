import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# API Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
NVD_API_KEY = os.getenv("NVD_API_KEY")

def ensure_directories():
    """Create necessary directories if they don't exist."""
    for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
# Random seed for reproducibility
RANDOM_SEED = 42