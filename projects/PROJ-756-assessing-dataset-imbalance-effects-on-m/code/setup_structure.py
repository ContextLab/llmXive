"""
Setup script to create the project directory structure.
This module is invoked by main.py or run.sh to ensure all required
directories and placeholder files exist before processing begins.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the full project directory structure as defined in T001.
    Creates __init__.py and .gitkeep files where appropriate.
    """
    # Base project root (assumed to be the directory where this script is run)
    # If run as `python code/setup_structure.py`, we need to go up one level or rely on CWD
    # The task requires paths relative to project root.
    # We assume the script is run from the project root or the CWD is set correctly.
    
    # Define the root directory for this specific project instance
    # The task specifies: `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/`
    # However, the prompt says "Stay inside the project tree... relative to the project root".
    # Given the existing files are in `code/`, `tests/` at root, we assume the current
    # working directory IS the project root `projects/PROJ-756-...`.
    
    project_root = Path.cwd()
    
    # Directories to create
    dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "code",
        "tests",
        "artifacts",
        "results",
        "state",
        "logs",
        "logs/archive"
    ]
    
    for dir_path in dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py in all directories
    init_files = [
        "code",
        "tests",
        "data",
        "artifacts",
        "results",
        "state",
        "logs"
    ]
    
    for dir_path in init_files:
        full_path = project_root / dir_path / "__init__.py"
        if not full_path.exists():
            full_path.write_text(f"# Package: {dir_path}\n")
            print(f"Created init file: {full_path}")
    
    # Create .gitkeep in data subdirectories
    gitkeep_dirs = [
        "data/raw",
        "data/processed",
        "data/synthetic",
        "logs/archive"
    ]
    
    for dir_path in gitkeep_dirs:
        full_path = project_root / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.write_text("# Keep directory in version control\n")
            print(f"Created gitkeep: {full_path}")
    
    # Create requirements.txt in code/ if it doesn't exist
    req_file = project_root / "code" / "requirements.txt"
    if not req_file.exists():
        req_file.write_text("""pandas>=2.0.0
scikit-learn>=1.3.0
shap>=0.43.0
magpie>=3.0.0
datasets>=2.14.0
numpy>=1.24.0
scipy>=1.11.0
pyyaml>=6.0.0
cvxpy>=1.4.0
requests>=2.31.0
matplotlib>=3.7.0
seaborn>=0.12.0
ruff>=0.1.0
black>=23.0.0
pytest>=7.4.0
""")
        print(f"Created requirements.txt: {req_file}")
    
    # Create run.sh in root if it doesn't exist
    run_script = project_root / "run.sh"
    if not run_script.exists():
        run_script.write_text("""#!/bin/bash
# Entry point script for PROJ-756
# Constitution Principle I: Project must be immediately runnable

set -e

echo "Starting PROJ-756 pipeline..."

# Ensure Python environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: No virtual environment detected. Proceeding with system Python."
fi

# Run the main pipeline
python code/main.py --full-pipeline

echo "Pipeline execution completed."
""")
        run_script.chmod(0o755)
        print(f"Created run.sh: {run_script}")

def main():
    print("Initializing project structure...")
    create_directories()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()