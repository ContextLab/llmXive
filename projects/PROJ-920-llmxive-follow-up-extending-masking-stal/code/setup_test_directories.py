import os
from pathlib import Path

def main():
    """
    Creates the directory structure for tests:
    - tests/unit/
    - tests/integration/
    - tests/contract/
    
    This script is designed to be run from the project root:
    projects/PROJ-920-llmxive-follow-up-extending-masking-stal/
    """
    base_dir = Path("tests")
    subdirs = ["unit", "integration", "contract"]

    for subdir in subdirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py to ensure these are recognized as Python packages
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
        print(f"Created directory: {dir_path}")

    # Ensure the root tests directory exists
    base_dir.mkdir(parents=True, exist_ok=True)
    if not (base_dir / "__init__.py").exists():
        (base_dir / "__init__.py").touch()
    print(f"Created directory: {base_dir}")

if __name__ == "__main__":
    main()