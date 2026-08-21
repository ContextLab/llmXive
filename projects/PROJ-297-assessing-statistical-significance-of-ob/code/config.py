import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Configuration paths
BASE_DIR = Path(__file__).parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_RESULTS_DIR = BASE_DIR / "output" / "results"
OUTPUT_PLOTS_DIR = BASE_DIR / "output" / "plots"
OUTPUT_REPORTS_DIR = BASE_DIR / "output" / "reports"
OUTPUT_EXPLORATORY_DIR = BASE_DIR / "output" / "exploratory"

# Random seed for reproducibility
RANDOM_SEED = 42

# Default thresholds
CORRELATION_THRESHOLD = 0.3
PERMUTATIONS_COUNT = 2000
P_VALUE_FLOOR = 1e-10
P_VALUE_CEIL = 1.0 - 1e-10

# Dataset IDs (OpenML) - Verified Real Sources
# 15: Breast Cancer (WDBC)
# 29: Wine
# 167: Abalone
# 168: Breast Cancer Wisconsin (Prognostic)
# 169: Concrete Compressive Strength
DATASET_IDS = [15, 29, 167, 168, 169]

def get_config() -> Dict[str, Any]:
    """Return the configuration dictionary."""
    return {
        "paths": {
            "raw": str(DATA_RAW_DIR),
            "processed": str(DATA_PROCESSED_DIR),
            "results": str(OUTPUT_RESULTS_DIR),
            "plots": str(OUTPUT_PLOTS_DIR),
            "reports": str(OUTPUT_REPORTS_DIR),
            "exploratory": str(OUTPUT_EXPLORATORY_DIR),
        },
        "random_seed": RANDOM_SEED,
        "threshold": CORRELATION_THRESHOLD,
        "permutations": PERMUTATIONS_COUNT,
        "p_value_bounds": (P_VALUE_FLOOR, P_VALUE_CEIL),
        "dataset_ids": DATASET_IDS,
    }

def ensure_dirs():
    """Ensure all required directories exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        OUTPUT_RESULTS_DIR,
        OUTPUT_PLOTS_DIR,
        OUTPUT_REPORTS_DIR,
        OUTPUT_EXPLORATORY_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def save_config(config: Dict[str, Any], path: Optional[str] = None):
    """Save configuration to a YAML file."""
    if path is None:
        path = BASE_DIR / "config.yaml"
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if path is None:
        path = BASE_DIR / "config.yaml"
    if not os.path.exists(path):
        return get_config()
    with open(path, 'r') as f:
        return yaml.safe_load(f)
