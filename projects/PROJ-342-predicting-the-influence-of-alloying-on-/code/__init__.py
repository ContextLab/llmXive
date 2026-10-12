"""
Project package initializer.
Ensures that all required top‑level directories exist so that subsequent
pipeline scripts can rely on their presence without having to create them
repeatedly.
"""
import os
from pathlib import Path

# Determine the project root (one level above the `code` package)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# List of directories that must exist for the pipeline
REQUIRED_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "artifacts" / "models",
    PROJECT_ROOT / "artifacts" / "metrics",
    PROJECT_ROOT / "artifacts" / "reports",
    PROJECT_ROOT / "logs",
    PROJECT_ROOT / "tests",
]

# Create any missing directories
for _dir in REQUIRED_DIRS:
    _dir.mkdir(parents=True, exist_ok=True)
