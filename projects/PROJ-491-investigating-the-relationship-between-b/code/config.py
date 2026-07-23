import os
from pathlib import Path

def ensure_directories():
    """
    Ensure that the standard data directories exist.
    This is a helper function referenced by other modules.
    """
    base = Path.cwd()
    dirs = [
        base / "data" / "raw",
        base / "data" / "processed",
        base / "state"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
