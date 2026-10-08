import os
from pathlib import Path

def main():
    """
    Execute Source Directory Creation for llmXive project.
    Creates: src/generators, src/inference, src/analysis
    """
    base_dir = Path(__file__).parent.parent
    src_dir = base_dir / "src"
    
    directories = [
        src_dir / "generators",
        src_dir / "inference",
        src_dir / "analysis"
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Verify creation
    all_created = all(d.exists() and d.is_dir() for d in directories)
    if all_created:
        print("SUCCESS: All source directories created successfully.")
    else:
        print("ERROR: Some directories failed to create.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())