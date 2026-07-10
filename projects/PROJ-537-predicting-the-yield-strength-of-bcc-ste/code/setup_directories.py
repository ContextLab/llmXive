import os
import sys
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the required directories relative to the project root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/intermediate",
        "data/processed",
        "data/provenance",
        "data/results",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created_count = 0
    for dir_name in directories:
        target_path = base_dir / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            # Ensure it is actually a directory, not a file
            if not target_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {target_path}")
    
    print(f"Directory setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
