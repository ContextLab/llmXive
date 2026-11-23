"""
Script to create the required project directory structure for llmXive.
This implements T001b (and related setup tasks) by ensuring all necessary
directories exist under the project root.
"""
import os
from pathlib import Path

def main():
    """Create all required directories for the project."""
    root = Path(__file__).resolve().parent.parent
    
    # Directories for T001b
    dirs_to_create = [
        root / "code" / "env",
        root / "code" / "agents",
        root / "code" / "training",
        root / "code" / "analysis",
        # Directories for T001c (ensuring completeness)
        root / "code" / "tests",
        root / "docs",
        # Directories for T001d (ensuring completeness)
        root / "data" / "raw",
        root / "data" / "processed",
        # Ensure root directories exist if not already (T001a)
        root / "code",
        root / "specs",
        root / "tests",
        root / "data",
        root / "docs",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path.relative_to(root)}")
        else:
            print(f"Directory already exists: {dir_path.relative_to(root)}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    print(f"Project root: {root}")

if __name__ == "__main__":
    main()
