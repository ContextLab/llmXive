"""
Script to setup the data directory structure and .gitignore for large files.
This script creates the required directories and the .gitignore file.
"""
import os
from pathlib import Path

def setup_data_directories():
    """Create data/raw and data/processed directories."""
    base_path = Path(__file__).parent.parent
    data_path = base_path / "data"
    raw_path = data_path / "raw"
    processed_path = data_path / "processed"

    # Create directories if they don't exist
    raw_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)

    print(f"Created data directory structure at: {data_path}")
    print(f"  - {raw_path}")
    print(f"  - {processed_path}")

    return True

def create_gitignore():
    """Create .gitignore file in the data directory."""
    base_path = Path(__file__).parent.parent
    data_path = base_path / "data"
    gitignore_path = data_path / ".gitignore"

    gitignore_content = """# Data directories - exclude raw and processed data from version control
raw/
processed/
# Ignore temporary files
*.tmp
*.temp
# Ignore hidden files
.*
!.gitignore
"""

    with open(gitignore_path, 'w') as f:
        f.write(gitignore_content)

    print(f"Created .gitignore at: {gitignore_path}")
    return True

def main():
    """Main entry point for the script."""
    setup_data_directories()
    create_gitignore()
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()
