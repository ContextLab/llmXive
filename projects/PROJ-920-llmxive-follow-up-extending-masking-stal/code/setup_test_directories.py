import os
from pathlib import Path

def main():
    """
    Creates the directory structure for tests:
    - tests/unit/
    - tests/integration/
    - tests/contract/
    """
    base_dir = Path("tests")
    sub_dirs = ["unit", "integration", "contract"]

    for subdir in sub_dirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py to ensure they are treated as Python packages
        (dir_path / "__init__.py").touch()
        print(f"Created directory: {dir_path}")

    print("Test directory structure setup complete.")

if __name__ == "__main__":
    main()
