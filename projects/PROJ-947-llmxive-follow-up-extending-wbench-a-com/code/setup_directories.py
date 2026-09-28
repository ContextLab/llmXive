import os
import sys
from pathlib import Path

def ensure_directory(path: str) -> bool:
    """Ensure a directory exists, creating it if necessary."""
    dir_path = Path(path)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    return False

def ensure_checksums_file() -> bool:
    """Ensure the checksums.json file exists in data/."""
    data_dir = Path("data")
    checksums_file = data_dir / "checksums.json"
    if not checksums_file.exists():
        checksums_file.write_text("{}")
        return True
    return False

def verify_structure() -> bool:
    """Verify that the required directory structure exists."""
    required_dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data",
        "data/raw",
        "data/processed",
        "results"
    ]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"ERROR: Directory {dir_path} does not exist.")
            return False
    return True

def main():
    """Main entry point for directory setup."""
    print("Setting up directory structure...")
    
    # Ensure all required directories exist
    directories = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data",
        "data/raw",
        "data/processed",
        "results"
    ]
    
    for dir_path in directories:
        ensure_directory(dir_path)
        print(f"  Created/verified: {dir_path}")
    
    # Ensure checksums file exists
    ensure_checksums_file()
    print("  Created/verified: data/checksums.json")
    
    # Verify structure
    if verify_structure():
        print("Directory structure setup complete.")
        return 0
    else:
        print("ERROR: Directory structure verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())