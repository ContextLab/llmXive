import os
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
OUTPUT_ROOT = PROJECT_ROOT / "output"
LOGS_ROOT = PROJECT_ROOT / "logs"

# Configuration for deferred thresholds
SAMPLE_SIZE = 100
MIN_EVENTS = 10

def ensure_directories_exist():
    """Create necessary directory structure."""
    for d in [DATA_ROOT, OUTPUT_ROOT, LOGS_ROOT]:
        d.mkdir(parents=True, exist_ok=True)
    (DATA_ROOT / "raw").mkdir(exist_ok=True)
    (DATA_ROOT / "derived").mkdir(exist_ok=True)
    (DATA_ROOT / "validation").mkdir(exist_ok=True)

def get_config_summary() -> dict:
    return {
        "project_root": str(PROJECT_ROOT),
        "sample_size": SAMPLE_SIZE,
        "min_events": MIN_EVENTS
    }