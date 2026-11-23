import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "generated").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "findings").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "prompts").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "calibration").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "results").mkdir(parents=True, exist_ok=True)

# Random Seeds
RANDOM_SEED = 42

# Model Hyperparameters
MAX_TOKENS = 256
BATCH_SIZE = 1

# Scanner Timeouts (in seconds)
SCANNER_TIMEOUTS = {
    "bandit": 30,
    "semgrep": 60,
    "codeql_create": 120,
    "codeql_run": 60
}

# General Timeout
TIMEOUT_PER_SCAN = 60
