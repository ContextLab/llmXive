#!/usr/bin/env python3
"""
Script to set up the llmXive project directory structure.

This script creates the necessary directories (code/, data/, tests/)
and populates data subdirectories with .gitkeep files.
"""

import sys
import os

# Add the code directory to the path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
code_dir = os.path.join(project_root, "code")

if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from setup_project_structure import create_directory_structure, create_gitkeep_files


def main():
    """Main entry point for the setup script."""
    print("=" * 60)
    print("llmXive Project Setup")
    print("=" * 60)
    print()

    try:
        # Create directory structure
        print("Creating directory structure...")
        created_dirs = create_directory_structure(project_root)

        if created_dirs:
            print(f"Created {len(created_dirs)} directories:")
            for d in created_dirs:
                rel_path = os.path.relpath(d, project_root)
                print(f"  ✓ {rel_path}")
        else:
            print("  All directories already exist.")

        print()

        # Create .gitkeep files
        print("Creating .gitkeep files in data subdirectories...")
        created_files = create_gitkeep_files(project_root)

        if created_files:
            print(f"Created {len(created_files)} .gitkeep files:")
            for f in created_files:
                rel_path = os.path.relpath(f, project_root)
                print(f"  ✓ {rel_path}")
        else:
            print("  All .gitkeep files already exist.")

        print()
        print("=" * 60)
        print("Setup complete!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())