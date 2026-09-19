import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure and generate project_structure.txt.
    This script implements Task T001: Create project structure.
    """
    # Define the required directories relative to the project root
    # Based on T001 description: code/utils, data/raw, data/processed, data/results, data/metadata, tests/unit, tests/integration, docs
    # Also ensuring 'code' and 'data' and 'tests' root directories exist if not present
    directories = [
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    project_root = Path.cwd()

    print(f"Creating project structure in: {project_root}")

    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created: {full_path}")
        else:
            print(f"Exists: {full_path}")

    # Generate project_structure.txt as the deliverable artifact
    output_file = project_root / "project_structure.txt"
    
    # Run ls -R equivalent using pathlib to list the tree
    # We will write the directory listing to the file
    with open(output_file, 'w') as f:
        f.write(f"# Project Structure for PROJ-458\n")
        f.write(f"# Generated at: {Path.cwd()}\n\n")
        
        # Walk the relevant directories to simulate 'ls -R'
        # We only list the directories we created/managed in this task
        for dir_path in directories:
            full_path = project_root / dir_path
            f.write(f"\n{full_path}:\n")
            
            # List contents of this directory
            try:
                items = sorted(full_path.iterdir())
                if items:
                    for item in items:
                        if item.is_dir():
                            f.write(f"  {item.name}/\n")
                            # List sub-items if any (shallow)
                            sub_items = sorted(item.iterdir())
                            for sub_item in sub_items:
                                f.write(f"    {sub_item.name}\n")
                        else:
                            f.write(f"  {item.name}\n")
                else:
                    f.write("  (empty)\n")
            except PermissionError:
                f.write("  (permission denied)\n")
        
        f.write("\n")
        f.write("Summary:\n")
        f.write(f"- Total directories created/verified: {len(directories)}\n")
        f.write(f"- Output file: {output_file.name}\n")

    print(f"Project structure verification written to: {output_file}")
    print(f"Verification command: cat {output_file}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
