import os
from pathlib import Path

def main():
    """Create data subdirectories and .gitkeep files."""
    # Determine project root relative to this script location
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    data_dir = project_root / "data"

    subdirs = ["raw", "processed", "split"]

    for subdir in subdirs:
        target_path = data_dir / subdir
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep to ensure directory is tracked in git
        gitkeep_path = target_path / ".gitkeep"
        gitkeep_path.touch(exist_ok=True)
        
        print(f"Created directory: {target_path}")
        print(f"Created .gitkeep: {gitkeep_path}")

    print("Data subdirectories setup complete.")

if __name__ == "__main__":
    main()
