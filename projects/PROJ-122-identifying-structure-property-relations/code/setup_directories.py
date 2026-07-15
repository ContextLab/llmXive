import os
from pathlib import Path

def create_directories(base_path: str):
    """
    Create the required project directory structure.
    """
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/features",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "state/projects",
        "specs/001-structure-property-relationships/contracts"
    ]

    for d in dirs:
        path = Path(base_path) / d
        path.mkdir(parents=True, exist_ok=True)
        # Ensure __init__.py exists in code and tests subdirs for Python package recognition
        if d.startswith("code") or d.startswith("tests"):
            init_file = path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

if __name__ == "__main__":
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    create_directories(base)
