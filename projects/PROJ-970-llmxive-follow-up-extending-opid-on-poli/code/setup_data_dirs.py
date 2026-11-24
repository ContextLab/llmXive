"""
Helper module to create the required directory hierarchy for the project.
"""

import os
from pathlib import Path
from typing import List

REQUIRED_DIRS = [
    "src",
    "src/environment",
    "src/agent",
    "src/simulation",
    "src/analysis",
    "src/utils",
    "tests",
    "data",
    "data/raw",
    "data/raw/synthetic_graphs",
    "data/processed",
    "data/results",
    "figures",
]

def create_directories(root_path: str) -> List[Path]:
    """
    Create all directories listed in ``REQUIRED_DIRS`` under ``root_path``.
    Returns a list of the created Path objects.
    """
    created = []
    for rel in REQUIRED_DIRS:
        p = Path(root_path) / rel
        p.mkdir(parents=True, exist_ok=True)
        created.append(p)
    return created

def main() -> None:
    root = Path(__file__).resolve().parents[1]  # project root
    create_directories(str(root))
    print("Directory structure created.")