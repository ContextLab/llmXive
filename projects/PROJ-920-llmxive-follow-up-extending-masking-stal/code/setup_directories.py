import os
from pathlib import Path

def main():
    """
    Creates the required directory structure for the llmXive project.
    Specifically implements T001: Create data/raw/ directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    raw_data_dir = project_root / "data" / "raw"
    
    # Ensure the parent 'data' directory exists first
    raw_data_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Create the specific 'raw' directory
    raw_data_dir.mkdir(exist_ok=True)
    
    print(f"Created directory: {raw_data_dir}")

if __name__ == "__main__":
    main()