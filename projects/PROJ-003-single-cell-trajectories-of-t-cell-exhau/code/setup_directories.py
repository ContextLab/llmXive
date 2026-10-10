import os
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project.

    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/results/
    - tests/unit/
    - tests/integration/

    Returns:
        Path: The project root path where directories were created.
    """
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration",
    ]
    root = Path(".").resolve()
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
    return root

if __name__ == "__main__":
    setup_directories()
