import os
from pathlib import Path

def main():
    """
    Create the canonical project layout for the mindfulness-DMN analysis.
    Ensures all required directories and package __init__.py files exist.
    """
    # Define all required directories
    # We include both top-level 'code/' and 'code/src/' to maintain 
    # compatibility with various import styles found in the project.
    directories = [
        "code/config",
        "code/utils",
        "code/src/config",
        "code/src/utils",
        "code/src/analysis",
        "code/src/datasets",
        "code/src/preprocessing",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "docs",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "figures",
        "results",
    ]

    print("Creating project directory structure...")
    for dir_path in directories:
        p = Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {dir_path}")

    # Define where __init__.py files should be to make them Python packages
    packages = [
        "code/config",
        "code/utils",
        "code/src",
        "code/src/config",
        "code/src/utils",
        "code/src/analysis",
        "code/src/datasets",
        "code/src/preprocessing",
    ]

    for pkg_path in packages:
        init_file = Path(pkg_path) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")

    print("Project layout initialized successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
