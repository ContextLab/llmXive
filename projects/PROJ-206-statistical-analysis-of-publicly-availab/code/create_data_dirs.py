import os
import sys
from pathlib import Path

def main():
    """
    Create the data directory structure at the project root.
    Specifically creates 'data/' and its subdirectories 'raw/' and 'processed/'.
    """
    # Determine project root (assuming script is in code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    # Create directories if they don't exist
    data_root.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created data directory structure at: {data_root}")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")
    
    # Verify existence
    assert data_root.exists(), "Failed to create data directory"
    assert raw_dir.exists(), "Failed to create data/raw directory"
    assert processed_dir.exists(), "Failed to create data/processed directory"
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
