import os
from pathlib import Path
import sys
from config import PROJECT_ROOT

def ensure_dir(path: Path) -> None:
    """Ensure the given directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)

def main() -> None:
    """Create the required data directory structure."""
    data_raw = PROJECT_ROOT / "data" / "raw"
    data_processed = PROJECT_ROOT / "data" / "processed"

    ensure_dir(data_raw)
    ensure_dir(data_processed)

    print(f"Created directories: {data_raw}, {data_processed}")

if __name__ == "__main__":
    main()
