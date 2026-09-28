import os
from pathlib import Path

def create_directories():
    """Create the directory hierarchy defined in the plan."""
    base_dirs = [
        "code/data",
        "code/analysis",
        "code/config",
        "code/tests",
        "data/raw",
        "data/results",
        "specs/001-social-support-resilience",
        "code/utils",
        "code/logs"
    ]

    for dir_path in base_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def main():
    create_directories()
    print("Project structure created successfully.")

if __name__ == "__main__":
    main()
