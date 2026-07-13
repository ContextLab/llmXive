import os
from pathlib import Path

def main():
    base_path = Path(__file__).parent
    
    # Define directory structures
    dirs = [
        # Code structure
        "code",
        "code/agents",
        "code/dataset",
        "code/analysis",
        "code/utils",
        
        # Data structure
        "data",
        "data/raw",
        "data/derived",
        "data/logs",
        "data/results",
        
        # Test structure
        "tests",
        "tests/unit",
        "tests/integration",
    ]

    for dir_path in dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create __init__.py files to make directories Python packages
    init_files = []
    for dir_path in dirs:
        full_path = base_path / dir_path / "__init__.py"
        if not full_path.exists():
          full_path.touch()
          init_files.append(str(full_path))
    
    if init_files:
        print(f"Created __init__.py files in {len(init_files)} directories.")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()