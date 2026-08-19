import os
import subprocess
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Creates the required directory structure for the project.
    
    Args:
        base_path: The root path where directories should be created.
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
    
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def generate_tree_output(base_path: Path, output_file: Path) -> None:
    """
    Executes the 'tree' or 'find' command to verify directory creation
    and saves the output to a file.
    
    Args:
        base_path: The root path to list.
        output_file: The file path where the tree output will be saved.
    """
    try:
        # Try 'tree' command first
        result = subprocess.run(
            ["tree", str(base_path)],
            capture_output=True,
            text=True,
            check=True
        )
        output_content = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to 'find' command if 'tree' is not available
        print("'tree' command not found, using 'find' command as fallback.")
        try:
            result = subprocess.run(
                ["find", str(base_path), "-type", "d"],
                capture_output=True,
                text=True,
                check=True
            )
            output_content = result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to generate directory listing: {e.stderr}")
    
    # Write the output to the specified file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_content)
    
    print(f"Directory structure verification saved to: {output_file}")

def main() -> None:
    """Main entry point for project structure setup."""
    # Define the project root path based on the task description
    project_root = Path("projects/PROJ-044-evaluating-the-effectiveness-of-differen")
    
    # Ensure the project root exists
    project_root.mkdir(parents=True, exist_ok=True)
    
    print(f"Setting up project structure in: {project_root}")
    
    # Create directories
    create_directories(project_root)
    
    # Generate and save tree output
    tree_output_path = project_root / "tree_output.txt"
    generate_tree_output(project_root, tree_output_path)
    
    print("Project structure setup completed successfully.")

if __name__ == "__main__":
    main()
