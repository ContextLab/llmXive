import os
from pathlib import Path

def main():
    """
    Create spec directories for the project.
    Specifically creates specs/001-neural-correlates-of-anticipatory-reward/
    """
    project_root = Path(__file__).resolve().parent.parent
    spec_dir = project_root / "specs" / "001-neural-correlates-of-anticipatory-reward"
    
    # Create the directory if it doesn't exist
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify creation
    if spec_dir.exists():
        print(f"Successfully created spec directory: {spec_dir}")
    else:
        raise RuntimeError(f"Failed to create spec directory: {spec_dir}")

if __name__ == "__main__":
    main()