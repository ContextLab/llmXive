"""
Project Structure Creation Script.
Implements T001: Create project structure per implementation plan.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the project.
    Ensures all necessary folders exist with placeholder files where appropriate.
    """
    # Define the project root (current directory)
    project_root = Path(".")
    
    # Define the required directory structure
    directories = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "figures",
        "reports",
        "tests",
        "docs",
        "specs",
        ".github/workflows"
    ]
    
    # Create directories
    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create placeholder files to ensure the structure is recognized by version control
    # and to provide a base for future implementation
    placeholder_files = {
        "code/__init__.py": "",
        "code/config.py": "# Configuration module\n",
        "code/data_model.py": "# Data models\n",
        "code/ingest.py": "# Data ingestion\n",
        "code/preprocess.py": "# Preprocessing\n",
        "code/analysis.py": "# Statistical analysis\n",
        "code/report.py": "# Report generation\n",
        "code/main.py": "# Main pipeline entry point\n",
        "tests/__init__.py": "",
        "tests/test_ingest.py": "# Ingestion tests\n",
        "tests/test_preprocess.py": "# Preprocessing tests\n",
        "tests/test_analysis.py": "# Analysis tests\n",
        "data/.gitkeep": "",
        "data/raw/.gitkeep": "",
        "data/interim/.gitkeep": "",
        "data/processed/.gitkeep": "",
        "figures/.gitkeep": "",
        "reports/.gitkeep": "",
        "docs/.gitkeep": "",
        "specs/.gitkeep": "",
        ".github/workflows/.gitkeep": ""
    }
    
    created_files = []
    for file_path, content in placeholder_files.items():
        full_path = project_root / file_path
        if not full_path.exists():
            full_path.write_text(content)
            created_files.append(file_path)
            print(f"Created file: {full_path}")
        else:
            print(f"File already exists: {full_path}")
    
    print("\nProject structure creation complete.")
    print(f"Created {len(created_dirs)} directories and {len(created_files)} placeholder files.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
