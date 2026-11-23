import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ID = "PROJ-164-neural-oscillations-as-a-biomarker-for-p"

# Directories
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_SYNTHETIC = PROJECT_ROOT / "data" / "synthetic"
MODELS = PROJECT_ROOT / "models"
DOCS = PROJECT_ROOT / "docs"
LOGS = PROJECT_ROOT / "logs"
STATE = PROJECT_ROOT / "state" / "projects"
CODE = PROJECT_ROOT / "code"
TESTS = PROJECT_ROOT / "tests"
SPECS = PROJECT_ROOT / "specs"

# Ensure directories exist
def ensure_dirs():
    dirs = [DATA_RAW, DATA_PROCESSED, DATA_SYNTHETIC, MODELS, DOCS, LOGS, STATE, CODE, TESTS, SPECS]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Constants
BANDS = ['delta', 'theta', 'alpha', 'beta', 'gamma']
LOWER_FREQ_HZ = 1.0
ALPHA = 0.05
R2_EXPECTED = 0.1
POWER_TARGET = 0.80

# Initialize directories on import
ensure_dirs()
