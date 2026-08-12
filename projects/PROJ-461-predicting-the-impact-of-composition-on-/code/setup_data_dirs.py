"""
Setup script to create the required directory structure for the project.
This ensures data/, models/, reports/, and logs/ directories exist.
"""
import os
from pathlib import Path


def setup_directories():
    """Create the required directory structure."""
    root = Path(__file__).parent.parent
    
    directories = [
        root / "data",
        root / "models",
        root / "reports",
        root / "logs",
        # Ensure code subdirectories exist as per T001
        root / "code" / "data",
        root / "code" / "features",
        root / "code" / "models",
        root / "code" / "analysis",
        root / "code" / "utils",
        root / "tests" / "unit",
        root / "tests" / "contract",
        root / "tests" / "integration",
        root / "docs",
        root / "docs" / "deviations",
        root / "docs" / "kickback_requests",
        root / "contracts",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory}")
        else:
            print(f"Directory exists: {directory}")
    
    print(f"\nSetup complete. Created {created_count} new directories.")
    return created_count


def main():
    """Entry point for the script."""
    setup_directories()


if __name__ == "__main__":
    main()