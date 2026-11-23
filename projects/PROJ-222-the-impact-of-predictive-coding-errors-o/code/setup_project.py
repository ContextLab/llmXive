import os
import sys
from pathlib import Path


def create_directories():
    """
    Create the project directory structure as per the implementation plan.
    Creates: data/raw, data/processed, code, figures, analysis, contracts
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "code",  # Already exists but ensures presence
        base_dir / "figures",
        base_dir / "analysis",
        base_dir / "contracts",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return created_count


if __name__ == "__main__":
    create_directories()
