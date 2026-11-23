import os
from pathlib import Path

def setup_directories():
    """
    Creates the required directory structure for the project:
    - data/raw
    - data/processed
    
    Ensures that .gitkeep files are present in each directory to preserve
    them in version control.
    """
    # Determine the project root based on the known structure
    # We assume this script runs from the project root or the code/ directory
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent if current_dir.name == 'code' else current_dir

    data_root = project_root / 'data'
    raw_dir = data_root / 'raw'
    processed_dir = data_root / 'processed'

    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files
    (raw_dir / '.gitkeep').touch()
    (processed_dir / '.gitkeep').touch()

    print(f"Created directories: {raw_dir}, {processed_dir}")
    print("Created .gitkeep files to preserve directory structure.")

if __name__ == "__main__":
    setup_directories()