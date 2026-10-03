"""
Utilities for ingestion tasks.
"""
import os
from datetime import datetime
from pathlib import Path

def ensure_dir(dir_path: str):
    """Ensure a directory exists, creating it if necessary."""
    path = Path(dir_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    return path