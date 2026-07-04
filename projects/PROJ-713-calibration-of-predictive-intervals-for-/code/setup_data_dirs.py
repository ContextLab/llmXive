import os
from pathlib import Path
import sys
from config import PROJECT_ROOT

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    os.makedirs(path, exist_ok=True)

def main() -> None:
    """Create the required data directory structure."""
    # Define paths relative to project root
    data_root = PROJECT_ROOT / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    # Ensure directories exist
    ensure_dir(raw_dir)
    ensure_dir(processed_dir)
    
    # Log creation (using standard print for script execution visibility)
    print(f"Created data directories:")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")

if __name__ == "__main__":
    main()
