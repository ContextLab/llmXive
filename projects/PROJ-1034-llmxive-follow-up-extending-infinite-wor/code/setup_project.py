import os
import sys
import json

def create_directory(path: str) -> None:
    """Create a directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def create_file(path: str, content: str = "") -> None:
    """Create a file with optional content."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created file: {path}")

def main() -> None:
    """
    Create the project directory structure for llmXive.
    Implements T001: Create project structure per implementation plan.
    
    Required structure:
    - src/sim
    - src/analysis
    - src/data
    - src/cli
    - src/tests
    """
    # Define the base directories relative to project root
    # Note: The task description mentions 'src/' but the existing API surface
    # uses 'code/' as the root for modules (e.g., code/sim/eco_director.py).
    # We will create the structure under 'code/' to match the existing API.
    
    base_dir = "code"
    structure = [
        "sim",
        "analysis",
        "data",
        "data/raw",
        "data/processed",
        "cli",
        "tests",
        "tests/unit",
        "tests/integration",
        "figures",
        "specs"
    ]

    for dir_path in structure:
        full_path = os.path.join(base_dir, dir_path)
        create_directory(full_path)

    # Create __init__.py files to make them packages
    package_dirs = [
        "sim", "analysis", "data", "cli", "tests",
        "tests/unit", "tests/integration"
    ]

    for pkg_dir in package_dirs:
        init_path = os.path.join(base_dir, pkg_dir, "__init__.py")
        create_file(init_path, "# Package initialization\n")

    # Create placeholder README in data directories
    create_file(os.path.join(base_dir, "data", "README.md"), 
                "# Data Directory\n\nThis directory stores raw and processed data.")
    
    create_file(os.path.join(base_dir, "data", "raw", "README.md"), 
                "# Raw Data\n\nUnprocessed data files go here.")
                
    create_file(os.path.join(base_dir, "data", "processed", "README.md"), 
                "# Processed Data\n\nAggregated and analyzed data files go here.")

    print("\nProject structure created successfully.")
    print(f"Root: {os.path.abspath(base_dir)}")

if __name__ == "__main__":
    main()