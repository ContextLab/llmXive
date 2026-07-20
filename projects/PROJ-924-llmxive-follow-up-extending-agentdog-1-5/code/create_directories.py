import os
from pathlib import Path

def ensure_directories():
    """
    Creates all required directories for the llmXive project structure.
    This function ensures the existence of:
    - code/, tests/, data/raw/, data/processed/, data/test/
    - specs/, docs/, specs/001-llmxive-drift-detection/
    """
    base_path = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/test",
        "specs",
        "docs",
        "specs/001-llmxive-drift-detection"
    ]
    
    created_dirs = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
    
    return created_dirs

def main():
    """Entry point for directory creation script."""
    print("Creating project directories...")
    created = ensure_directories()
    for d in created:
        print(f"  Created: {d}")
    print("Directory setup complete.")

if __name__ == "__main__":
    main()