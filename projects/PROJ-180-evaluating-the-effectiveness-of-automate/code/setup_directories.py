"""
Script to initialize the project directory structure for the llmXive automated science pipeline.
Creates the required directories and empty __init__.py/config.yaml files as per T001a and T001b.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base directory (project root)
    # We assume the script is run from the project root or code/ directory
    # We normalize to the parent of this script if it's in code/, otherwise current dir
    script_path = Path(__file__).resolve()
    if script_path.name == "setup_directories.py" and script_path.parent.name == "code":
        base_dir = script_path.parent.parent
    else:
        base_dir = Path.cwd()

    # Define directories to create
    # T001a: code/, data/raw, data/processed, results, specs/
    # Note: code/ and specs/ might already exist, but we ensure them.
    # data/ needs subdirectories raw and processed.
    
    directories = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "results",
        base_dir / "specs",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    # T001b: Create empty __init__.py in code/ and data/ subfolders
    # We need __init__.py in: code/, data/, data/raw/, data/processed/
    init_files = [
        base_dir / "code" / "__init__.py",
        base_dir / "data" / "__init__.py",
        base_dir / "data" / "raw" / "__init__.py",
        base_dir / "data" / "processed" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created empty file: {init_file}")
        else:
            print(f"File already exists: {init_file}")

    # T001b: Create empty config.yaml in code/
    config_file = base_dir / "code" / "config.yaml"
    if not config_file.exists():
        # Create a minimal empty config or a basic structure
        # The task says "empty", but a YAML file with just comments or empty string is valid.
        # We'll write an empty string to be safe, or a minimal header if preferred.
        # "empty" usually implies 0 bytes or just whitespace.
        config_file.write_text("")
        print(f"Created empty file: {config_file}")
    else:
        print(f"File already exists: {config_file}")

    # T001b: Create empty config.yaml in data/ (implied by "in code/ and data/ subfolders")
    data_config_file = base_dir / "data" / "config.yaml"
    if not data_config_file.exists():
        data_config_file.write_text("")
        print(f"Created empty file: {data_config_file}")
    else:
        print(f"File already exists: {data_config_file}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
