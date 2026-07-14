import os
from pathlib import Path

def setup_data_directories():
    """
    Create the required data directory structure for the project.
    Creates:
      - data/raw/
      - data/processed/
      - data/results/
      - data/neural/processed/ (for US1 specific outputs)
      - data/text/ (for US1 text data)
      - tests/
      - state/
      - logs/
    """
    base_dir = Path(__file__).parent.parent
    data_root = base_dir / "data"
    
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/neural/processed",
        "data/text",
        "tests",
        "state",
        "logs",
        "figures"
    ]
    
    created_count = 0
    for rel_path in directories:
        full_path = base_dir / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for rel_path in directories:
        keep_file = base_dir / rel_path / ".gitkeep"
        if not keep_file.exists():
            keep_file.touch()
    
    print(f"\nSetup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    setup_data_directories()
