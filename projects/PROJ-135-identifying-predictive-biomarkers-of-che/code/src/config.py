import os
from pathlib import Path

# Project Root
# Assuming the code is run from the project root or 'code' directory
# Adjust based on actual project structure if needed
if "code" in str(Path(__file__).parent):
    PROJECT_ROOT = Path(__file__).parent.parent
else:
    PROJECT_ROOT = Path(__file__).parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_META = RESULTS_DIR / "meta_analysis"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-chemo-biomarker-discovery"
CONTRACTS_DIR = SPECS_DIR / "contracts"
STATE_DIR = PROJECT_ROOT / "state"

# Configuration Constants
RANDOM_SEED = 42
FDR_THRESHOLD = 0.05
CPU_LIMIT = None # Set to number of cores if needed
MEMORY_LIMIT_MB = 16000 # 16GB default
MAX_VARIANCE_GENES = 5000
MAX_RUNTIME_HOURS = 5

# Feasibility Gate Constants
MIN_TCQA_TYPES = 3

def ensure_directories():
    """Creates all required directories if they do not exist."""
    dirs = [DATA_RAW, DATA_PROCESSED, RESULTS_DIR, RESULTS_META, STATE_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)