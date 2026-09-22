import os
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure:
    - src/ (source code)
    - tests/ (test suite)
    - data/ (raw and processed data)
    - output/ (analysis results and reports)
    """
    base_dir = Path(__file__).parent
    
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "output/temporal_profiles",
        "contracts",
        "specs"
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create placeholder .gitkeep files to ensure directories are tracked
    for dir_path in directories:
        full_path = base_dir / dir_path
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {full_path}")

if __name__ == "__main__":
    create_directories()
    print("Project structure initialization complete.")