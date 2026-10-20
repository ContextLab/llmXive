import seed
import os
import sys
from pathlib import Path

def main() -> int:
    """
    Create required project directories.
    """
    required_dirs = [
        "data/raw",
        "data/processed",
        "results",
        "logs",
        "code",
        "tests"
    ]
    for d in required_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    return 0
