"""
Project structure and directory setup for the llmXive pipeline.
Creates the required directory hierarchy and empty __init__.py files.
"""
import os
from pathlib import Path


def setup_data_directories():
    """
    Create the required directory structure for the project.
    Creates:
      - code/
      - src/
      - tests/
      - data/raw/
      - data/processed/
      - data/derived/
    Also creates empty __init__.py files in all src/ subfolders.
    """
    base_dir = Path(__file__).parent.parent
    directories = [
        base_dir / "code",
        base_dir / "src",
        base_dir / "tests",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "derived",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    # Create __init__.py files in src/ subfolders
    src_dir = base_dir / "src"
    subfolders = ["analysis", "extraction", "utils"]
    for subfolder in subfolders:
        init_file = src_dir / subfolder / "__init__.py"
        init_file.parent.mkdir(parents=True, exist_ok=True)
        init_file.touch(exist_ok=True)
        print(f"Created __init__.py: {init_file}")

    # Create __init__.py in tests/
    tests_dir = base_dir / "tests"
    (tests_dir / "__init__.py").touch(exist_ok=True)
    print(f"Created __init__.py: {tests_dir / '__init__.py'}")

    # Create __init__.py in src/ itself
    (src_dir / "__init__.py").touch(exist_ok=True)
    print(f"Created __init__.py: {src_dir / '__init__.py'}")


def create_config_files():
    """
    Create basic configuration files if they don't exist.
    """
    base_dir = Path(__file__).parent.parent
    config_files = [
        base_dir / "code" / ".flake8",
        base_dir / "code" / "pyproject.toml",
    ]

    for config_file in config_files:
        if not config_file.exists():
            config_file.touch()
            print(f"Created empty config file: {config_file}")
        else:
            print(f"Config file already exists: {config_file}")


def main():
    """
    Main entry point for running the setup script.
    """
    print("Setting up project structure...")
    setup_data_directories()
    create_config_files()
    print("Project structure setup complete.")


if __name__ == "__main__":
    main()
