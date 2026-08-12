"""
Project setup script to create the directory structure for the metallic glass density prediction project.
"""
import os
from pathlib import Path


def setup_directories():
    """Create the required directory structure."""
    base_path = Path(".")
    directories = [
        "code/data",
        "code/features",
        "code/models",
        "code/analysis",
        "data",
        "models",
        "reports",
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]

    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    print("Project structure setup complete.")


def main():
    """Entry point for the setup script."""
    setup_directories()


if __name__ == "__main__":
    main()
