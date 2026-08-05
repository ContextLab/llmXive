import os
from pathlib import Path

# Constants defined in task T012
RANDOM_SEED = 42
DATA_ROOT = "data"
RESULTS_ROOT = "results"

def ensure_directories():
    """Ensure all required project directories exist."""
    dirs = [
        DATA_ROOT,
        os.path.join(DATA_ROOT, "raw"),
        os.path.join(DATA_ROOT, "processed"),
        RESULTS_ROOT,
        os.path.join(RESULTS_ROOT, "models"),
        os.path.join(RESULTS_ROOT, "figures"),
        "tests",
        "contracts",
        "logs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
