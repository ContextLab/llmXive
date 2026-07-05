"""
Setup script to create the specs/ directory structure and placeholder files
for the llmXive research project.
"""
import os
import sys
from spec_utils import create_specs_structure


def main():
    """
    Main entry point to create the specs directory structure.
    """
    # Define the project root (assuming this script is in code/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    specs_dir = os.path.join(project_root, "specs")

    print(f"Creating specs directory structure at: {specs_dir}")

    # Create the directory structure
    create_specs_structure(specs_dir)

    print("Specs directory structure created successfully.")


if __name__ == "__main__":
    main()