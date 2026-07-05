import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the 'results/reports' directory."""
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    reports_dir = results_dir / "reports"
    create_directory(reports_dir)
    print(f"Created directory: {reports_dir}")

if __name__ == "__main__":
    main()
