import os
from pathlib import Path

def ensure_dirs():
    """Ensure all necessary directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "artifacts",
        "figures"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

# Add other config variables as needed
RANDOM_SEED = 42
DATA_PATH = "data/raw"
OUTPUT_PATH = "data/processed"