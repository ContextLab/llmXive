import seed
import os
from pathlib import Path
from typing import List

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "results",
    "logs",
    "code",
    "tests"
]

def create_directory_structure() -> None:
    """
    Create the required directory structure for the project.

    This function iterates over :data:`REQUIRED_DIRS` and ensures each path
    exists as a directory. Missing parents are created automatically
    (``parents=True``) and no error is raised if the directory already
    exists (``exist_ok=True``).

    The function is idempotent – calling it multiple times has the same
    effect as calling it once.
    """
    for dir_path in REQUIRED_DIRS:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
