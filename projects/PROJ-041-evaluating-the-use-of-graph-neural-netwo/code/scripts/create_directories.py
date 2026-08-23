import os
import sys

def ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Create the full project directory structure."""
    # Base directories
    dirs = [
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "tests/integration",
        "tests/unit",
    ]

    for d in dirs:
        ensure_dir(d)

    print("Project directory structure created successfully.")

if __name__ == "__main__":
    main()
