import os
from pathlib import Path
from setup_directories import create_directory, main as setup_main

def main():
    """Create the results/reports/ directory for storing model performance reports."""
    base_path = Path("results")
    reports_path = base_path / "reports"
    create_directory(reports_path)
    print(f"Directory created: {reports_path}")

if __name__ == "__main__":
    main()