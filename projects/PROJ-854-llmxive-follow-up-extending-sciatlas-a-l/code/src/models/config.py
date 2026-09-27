import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data"
ARTIFACT_PATH = BASE_DIR / "artifacts"
SPEC_PATH = BASE_DIR / "specs"

# Constants
SEED = 42
MAX_BUFFER_ROWS = 10000  # Memory buffer limit
MAX_RAM_GB = 7.0

# Ensure directories exist
DATA_PATH.mkdir(parents=True, exist_ok=True)
ARTIFACT_PATH.mkdir(parents=True, exist_ok=True)
(DATA_PATH / "raw").mkdir(parents=True, exist_ok=True)
(DATA_PATH / "processed").mkdir(parents=True, exist_ok=True)
(ARTIFACT_PATH / "results").mkdir(parents=True, exist_ok=True)
(ARTIFACT_PATH / "plots").mkdir(parents=True, exist_ok=True)