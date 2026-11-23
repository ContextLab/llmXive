"""
T001: Python implementation of project structure initialization.
Provides programmatic creation of directories and tree generation.
"""
import os
import subprocess
from pathlib import Path
from typing import List, Optional

def create_directories(base_path: Path) -> bool:
    """
    Creates the required directory hierarchy for the project.
    
    Args:
        base_path: The root path where the project directories will be created.
                   Corresponds to projects/PROJ-044-evaluating-the-effectiveness-of-differen
    
    Returns:
        True if all directories were created successfully, False otherwise.
    """
    directories = [
        "code/data",
        "code/training",
        "code/analysis",
        "code/models",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/partitions",
        "results",
        "artifacts"
    ]

    created = True
    for dir_name in directories:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            created = False
    
    return created

def generate_tree_output(base_path: Path, output_file: Optional[Path] = None) -> bool:
    """
    Generates a directory tree visualization and saves it to a file.
    
    Args:
        base_path: The root path to visualize.
        output_file: Optional path to save the tree output. If None, prints to stdout.
    
    Returns:
        True if successful, False otherwise.
    """
    # Try to use the 'tree' command first
    try:
        result = subprocess.run(
            ["tree", str(base_path)],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to 'find' if 'tree' is not available
        print("Warning: 'tree' command not found. Using 'find' as fallback.")
        try:
            result = subprocess.run(
                ["find", str(base_path), "-type", "d"],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error generating tree output: {e}")
            return False

    if output_file:
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Tree output saved to: {output_file}")
        except OSError as e:
            print(f"Error writing to {output_file}: {e}")
            return False
    else:
        print(output)
    
    return True

def main():
    """
    Main entry point for the project structure initialization script.
    """
    # Define the project root as per task requirements
    project_root = Path("projects/PROJ-044-evaluating-the-effectiveness-of-differen")
    
    print(f"Initializing project structure at: {project_root}")
    
    # Create directories
    if not create_directories(project_root):
        print("Failed to create some directories. Exiting.")
        return 1
    
    # Generate tree output
    tree_output_path = project_root / "tree_output.txt"
    if not generate_tree_output(project_root, tree_output_path):
        print("Failed to generate tree output. Exiting.")
        return 1
    
    print("Project structure initialization completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())