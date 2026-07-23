import os
from pathlib import Path

# Project Root: Assumes code/ is one level deep from root
# If running from code/, adjust accordingly.
# Standard assumption: PROJECT_ROOT is the repo root.
_current_file = Path(__file__).resolve()
_code_dir = _current_file.parent
PROJECT_ROOT = _code_dir.parent

# Configuration Keys
VARIANCE_THRESHOLD = 0.01  # Default threshold for variance flagging
BATCH_SIZE = 1             # CPU batch size default
CPU_OFFLOAD_LIMIT = 2048   # MB
SEED = 42

# Paths
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_DIR = DATA_DIR / "prompts"
MODELS_DIR = DATA_DIR / "models"
OUTPUTS_DIR = DATA_DIR / "outputs"
RESULTS_DIR = DATA_DIR / "results"
REPORTS_DIR = DATA_DIR / "reports"
FIGURES_DIR = DATA_DIR / "figures"
