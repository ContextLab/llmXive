import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    This script ensures that docs/ and docs/reports/ directories exist.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define directories to create
    docs_dir = project_root / "docs"
    reports_dir = project_root / "docs" / "reports"
    
    # Create directories if they don't exist
    docs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created directories: {docs_dir}, {reports_dir}")
    print("Directory structure verification successful.")

if __name__ == "__main__":
    main()