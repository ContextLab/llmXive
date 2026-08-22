import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Project root relative to this file
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
OUTPUT_RESULTS_DIR = ROOT_DIR / "output" / "results"
OUTPUT_PLOTS_DIR = ROOT_DIR / "output" / "plots"
OUTPUT_REPORTS_DIR = ROOT_DIR / "output" / "reports"
STATE_DIR = ROOT_DIR / "state" / "projects"

# Random seed for reproducibility (Master Seed)
MASTER_SEED = 42

# Default thresholds
DEFAULT_THRESHOLD = 0.3
DEFAULT_PERMUTATIONS = 2000

# Runtime limits (seconds)
MAX_RUNTIME_SECONDS = 21600

# UCI Dataset Configs (Verified URLs)
# Note: T005/T006 logic handles fallback if these fail or yield < 20 continuous vars
UCI_DATASETS = {
    "wine": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
        "header": None,
        "sep": ","
    },
    "abalone": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data",
        "header": None,
        "sep": ","
    },
    "breast_cancer_wisconsin": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/breast-cancer-wisconsin.data",
        "header": None,
        "sep": ","
    },
    "student_performance": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00218/Student%20Performance%20Data.zip", # Handling zip
        "type": "zip",
        "files": ["student-mat.csv"]
    },
    "air_quality": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00360/AirQualityUCI.zip",
        "type": "zip",
        "files": ["AirQualityUCI.csv"]
    },
    "concrete_compressive_strength": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Data.xls",
        "header": 0,
        "sep": None
    }
}

def get_config() -> Dict[str, Any]:
    """Return the full configuration dictionary."""
    return {
        "paths": {
            "raw": str(DATA_RAW_DIR),
            "processed": str(DATA_PROCESSED_DIR),
            "results": str(OUTPUT_RESULTS_DIR),
            "plots": str(OUTPUT_PLOTS_DIR),
            "reports": str(OUTPUT_REPORTS_DIR),
            "state": str(STATE_DIR)
        },
        "seeds": {
            "master": MASTER_SEED
        },
        "defaults": {
            "threshold": DEFAULT_THRESHOLD,
            "permutations": DEFAULT_PERMUTATIONS,
            "max_runtime": MAX_RUNTIME_SECONDS
        },
        "datasets": UCI_DATASETS
    }

def ensure_dirs() -> None:
    """Create all required directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        OUTPUT_RESULTS_DIR,
        OUTPUT_PLOTS_DIR,
        OUTPUT_REPORTS_DIR,
        STATE_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def save_config(config: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Save configuration to a YAML file."""
    if path is None:
        path = STATE_DIR / "config.yaml"
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if path is None:
        path = STATE_DIR / "config.yaml"
    if not path.exists():
        return get_config()
    with open(path, 'r') as f:
        return yaml.safe_load(f)
