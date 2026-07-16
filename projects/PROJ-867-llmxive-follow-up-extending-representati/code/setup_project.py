"""
Project setup script for llmXive follow-up: extending Representation Forcing for Structured Text Generation.

This script creates the required directory structure for the project:
projects/PROJ-867-llmxive-follow-up-extending-representati/

Subdirectories created:
- code/
- data/
- tests/
- docs/

Additionally creates test subdirectory skeletons:
- tests/unit/
- tests/contract/
- tests/integration/
"""
import os
import sys
from pathlib import Path


def create_directory_structure():
    """Create the project directory structure."""
    # Define the base project directory
    base_dir = Path("projects/PROJ-867-llmxive-follow-up-extending-representati")
    
    # Main subdirectories
    main_dirs = ["code", "data", "tests", "docs"]
    
    # Test subdirectories
    test_dirs = ["tests/unit", "tests/contract", "tests/integration"]
    
    # Create all directories
    for dir_path in main_dirs + test_dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py files for Python package recognition
    for dir_path in ["tests/unit", "tests/contract", "tests/integration", "code", "code/utils", "code/data", "code/models"]:
        full_path = base_dir / dir_path / "__init__.py"
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.touch()
        print(f"Created __init__.py: {full_path}")
    
    # Create README files for documentation
    readme_content = """# {dir_name}
    
    This directory is part of the llmXive follow-up project.
    """
    
    for dir_path in main_dirs:
        readme_file = base_dir / dir_path / "README.md"
        readme_file.write_text(readme_content.format(dir_name=dir_path))
        print(f"Created README.md: {readme_file}")
    
    print(f"\nProject structure created successfully at: {base_dir}")
    return base_dir


def main():
    """Main entry point for the setup script."""
    print("Starting project directory structure creation...")
    print(f"Current working directory: {os.getcwd()}")
    
    try:
        base_dir = create_directory_structure()
        print(f"\nSetup completed successfully!")
        print(f"Project root: {base_dir}")
        return 0
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())