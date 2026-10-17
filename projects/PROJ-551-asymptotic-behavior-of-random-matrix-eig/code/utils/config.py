import logging
from pathlib import Path

OUTLIER_TOLERANCE = 1e-10

def ensure_directories():
    """Ensure all required project directories exist."""
    dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("data/logs"),
        Path("data/figures"),
        Path("contracts"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_project_paths():
    """Return a dictionary of key project paths."""
    return {
        "raw": Path("data/raw"),
        "processed": Path("data/processed"),
        "logs": Path("data/logs"),
        "figures": Path("data/figures"),
        "contracts": Path("contracts"),
    }
