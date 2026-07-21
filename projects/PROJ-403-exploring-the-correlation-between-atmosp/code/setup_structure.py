import os
from pathlib import Path

def main():
    """Initialize the project directory structure."""
    dirs = [
        "code/src",
        "code/tests",
        "code/tests/unit",
        "code/tests/integration",
        "code/data",
        "code/data/processed",
        "code/figures",
        "code/logs",
        "code/report",
        "code/artifacts",
    ]

    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        # Create __init__.py in src and tests subdirectories
        if d.startswith("code/src") or d.startswith("code/tests"):
            init_file = Path(d) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("Project structure initialized.")

if __name__ == "__main__":
    main()