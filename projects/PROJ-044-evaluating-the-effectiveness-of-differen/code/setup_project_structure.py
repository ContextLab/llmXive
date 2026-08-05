"""
Project Structure Setup Script for llmXive PROJ-044.

This script creates the required directory structure for the
Evaluating the Effectiveness of Differential Privacy in Federated Learning project.
It ensures deterministic creation of all necessary folders for code, data, tests,
and results.
"""
import os
import sys
import subprocess
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Create the required project directory structure.

    Args:
        base_path: The root directory where the project structure will be created.
    """
    # Define the required directories relative to the base path
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
        "artifacts"
    ]

    created_count = 0
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nTotal directories created: {created_count}")
    return created_count

def generate_tree_output(base_path: Path, output_file: Path) -> None:
    """
    Generate a tree-like listing of the created directory structure and save it.

    Args:
        base_path: The root directory to list.
        output_file: The file path where the tree output will be saved.
    """
    # Try to use the 'tree' command if available, otherwise use 'find'
    try:
        # Attempt to run tree command
        result = subprocess.run(
            ["tree", "-a", "-I", "__pycache__|.git"],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            output_content = result.stdout
        else:
            raise FileNotFoundError("tree command not found")
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        # Fallback to 'find' command if tree is not available
        print("Note: 'tree' command not found. Using 'find' as fallback.")
        try:
            result = subprocess.run(
                ["find", ".", "-type", "d", "-not", "-path '*/\\.*'"],
                cwd=base_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Format the find output to look somewhat like a tree
                lines = result.stdout.strip().split('\n')
                formatted_lines = [lines[0]]  # Root
                for line in lines[1:]:
                    # Indent based on depth (count slashes)
                    depth = line.count('/')
                    indent = "    " * (depth - 1) if depth > 1 else ""
                    formatted_lines.append(f"{indent}└── {line.split('/')[-1]}" if indent else f"└── {line.split('/')[-1]}")
                output_content = "\n".join(formatted_lines)
            else:
                output_content = "Error: Could not generate directory listing."
        except Exception as e:
            output_content = f"Error generating directory listing: {str(e)}"

    # Write the output to the specified file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)

    print(f"Tree output saved to: {output_file}")

def main():
    """Main entry point for the project structure setup."""
    # Determine the project root.
    # We assume the script is run from the project root or that we are in
    # projects/PROJ-044-evaluating-the-effectiveness-of-differen/
    # The task description implies we are working inside:
    # projects/PROJ-044-evaluating-the-effectiveness-of-differen/
    
    # Let's assume the current working directory is the project root for this task.
    # If run from a higher level, we might need to adjust, but the task
    # specifically asks to create structure in the project directory.
    base_path = Path.cwd()
    
    print(f"Setting up project structure in: {base_path}")
    
    # Create directories
    create_directories(base_path)
    
    # Generate and save tree output
    output_file = base_path / "tree_output.txt"
    generate_tree_output(base_path, output_file)
    
    print("\nProject structure setup complete.")
    print(f"Verification file created: {output_file}")

if __name__ == "__main__":
    main()
