import os
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project.
    This function ensures that data, models, reports, and test directories exist.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        base_dir / "data",
        base_dir / "models",
        base_dir / "reports",
        base_dir / "logs",
        base_dir / "figures",
        base_dir / "code" / "data",
        base_dir / "code" / "features",
        base_dir / "code" / "models",
        base_dir / "code" / "analysis",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "contract",
        base_dir / "tests" / "integration",
        base_dir / "contracts",
        base_dir / "docs",
        base_dir / "docs" / "deviations",
        base_dir / "docs" / "kickback_requests",
        base_dir / "state",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def main():
    setup_directories()
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()