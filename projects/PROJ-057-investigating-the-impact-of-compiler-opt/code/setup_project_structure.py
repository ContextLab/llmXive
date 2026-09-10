"""
Project Structure Setup Script for PROJ-057-investigating-the-impact-of-compiler-opt

This script creates the required directory hierarchy for the compiler optimization
impact study project as specified in plan.md.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Create the project directory structure."""
    project_root = Path("projects/PROJ-057-investigating-the-impact-of-compiler-opt")

    # Define all required directories
    directories = [
        # Code directories
        project_root / "code" / "kernels",
        project_root / "code" / "benchmarks",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        
        # Data directories
        project_root / "data" / "raw",
        project_root / "data" / "intermediates",
        project_root / "data" / "results",
        
        # Test directories
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]

    # Create directories with parents
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {dir_path}")

    # Create __init__.py files for Python packages
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "code" / "kernels" / "__init__.py",
        project_root / "code" / "benchmarks" / "__init__.py",
        project_root / "code" / "analysis" / "__init__.py",
        project_root / "code" / "utils" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
        project_root / "tests" / "integration" / "__init__.py",
    ]

    for init_file in init_files:
        init_file.touch(exist_ok=True)
        print(f"Created: {init_file}")

    print(f"\nProject structure created successfully at: {project_root}")
    return True


def main():
    """Main entry point for the script."""
    print("Setting up project structure for PROJ-057-investigating-the-impact-of-compiler-opt...")
    print("=" * 70)
    
    try:
        success = create_directories()
        if success:
            print("\n" + "=" * 70)
            print("SUCCESS: All directories and package files created.")
            return 0
        else:
            print("\n" + "=" * 70)
            print("ERROR: Failed to create project structure.")
            return 1
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
