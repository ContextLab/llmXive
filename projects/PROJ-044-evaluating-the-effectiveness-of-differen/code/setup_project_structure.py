"""
Project Structure Setup Script for llmXive PROJ-044.

This script creates the required directory hierarchy for the
'Evaluating the Effectiveness of Differential Privacy in Federated Learning'
project and generates a deterministic verification file (tree_output.txt).
"""
import os
import sys
import subprocess
from pathlib import Path


def create_directories(base_path: Path) -> None:
    """
    Create the required directory structure.

    Args:
        base_path: The root directory where the project structure will be created.
    """
    required_dirs = [
        "code/data",
        "code/training",
        "code/analysis",
        "code/models",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/partitions",
        "results",
        "artifacts",
    ]

    for dir_path in required_dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")


def generate_tree_output(base_path: Path, output_file: Path) -> None:
    """
    Generate a deterministic tree listing of the created structure.

    Attempts to use the `tree` command if available, otherwise falls back
    to a Python-based directory walk to ensure the artifact is always created.

    Args:
        base_path: The root directory to list.
        output_file: The path where the tree output will be saved.
    """
    try:
        # Try using the 'tree' command
        result = subprocess.run(
            ["tree", str(base_path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        content = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: Generate a sorted list representation if 'tree' is not found
        lines = [f"Project Root: {base_path.name}"]
        lines.append("-" * 40)
        
        for root, dirs, files in os.walk(base_path):
            level = root.replace(str(base_path), '').count(os.sep)
            indent = ' ' * 2 * level
            subdir_name = os.path.basename(root)
            if subdir_name:
                lines.append(f"{indent}{subdir_name}/")
            
            sub_indent = ' ' * 2 * (level + 1)
            for file in sorted(files):
                lines.append(f"{sub_indent}{file}")
        
        content = "\n".join(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Tree output saved to: {output_file}")


def main() -> int:
    """
    Main entry point for the project setup script.
    
    Returns:
        0 on success, 1 on failure.
    """
    # Determine the project root based on the task requirements
    # The task specifies the project is at: projects/PROJ-044-evaluating-the-effectiveness-of-differen/
    # We assume the script is run from the repository root or the project root.
    # We will resolve the path relative to the current working directory.
    
    # The task requires creating structure in:
    # projects/PROJ-044-evaluating-the-effectiveness-of-differen/
    # However, usually scripts in `code/` are run from the repo root.
    # Let's assume the current working directory is the repo root.
    
    repo_root = Path.cwd()
    project_dir = repo_root / "projects" / "PROJ-044-evaluating-the-effectiveness-of-differen"
    
    # If the project directory doesn't exist, create it first
    project_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Setting up project structure at: {project_dir}")
    
    try:
        # 1. Create directories
        create_directories(project_dir)
        
        # 2. Generate verification file
        tree_output_path = project_dir / "tree_output.txt"
        generate_tree_output(project_dir, tree_output_path)
        
        print("Project structure setup completed successfully.")
        return 0
        
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
