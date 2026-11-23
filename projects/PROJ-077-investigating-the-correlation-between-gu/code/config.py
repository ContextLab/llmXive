import os
from pathlib import Path

INPUT_PATHS = {
    "microbiome": "data/raw/microbiome.csv",
    "cognitive": "data/raw/cognitive.csv",
    "dietary": "data/raw/dietary.csv"
}
RANDOM_SEED = 42
SAMPLE_LIMIT = 50000

DQS_REQUIRED = False
ALLOW_LOCAL_DATA = True

def ensure_directories():
    """Create necessary directories if they don't exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "logs",
        "figures"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
