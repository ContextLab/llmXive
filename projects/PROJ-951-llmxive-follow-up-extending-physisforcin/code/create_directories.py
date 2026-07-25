"""
Script to create the detailed directory structure for PROJ-951-llmxive-follow-up-extending-physisforcin.
Creates src/, tests/, data/ and all required subdirectories as per T001b.
"""
import os
from pathlib import Path

def main():
    # Define the project root based on the task description
    # T001 created: projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    # We assume the script runs from the repository root or code/ directory.
    # We will create the structure relative to the current working directory or a fixed project root.
    # Given T001 created 'code/', we assume we are inside 'code/' or creating inside it.
    
    # Let's define the base path as the current working directory if it looks like 'code',
    # otherwise we look for the specific project folder.
    # To be safe and consistent with T001, we will assume the script is run from the project root
    # or the 'code' directory. The task says "Create ... under projects/.../code/".
    # Since T001 created the root, we assume we are operating inside that root.
    
    base_path = Path.cwd()
    
    # Check if we are in the correct project code directory
    # If the current dir is 'code', we proceed. If it's the project root, we enter 'code'.
    if base_path.name == "code":
        project_code_root = base_path
    elif (base_path / "code").exists() and (base_path / "code").name == "code":
        project_code_root = base_path / "code"
    else:
        # Fallback: assume we are in the project root and need to create 'code' structure
        # But T001 says it created the root under 'projects/.../code/'.
        # Let's assume the script is run from the repository root.
        # We will create the structure in 'projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/'
        # But since we don't know the absolute path, we assume the user runs this from the 'code' directory
        # or the script adjusts.
        # To be robust, we'll try to find the 'code' folder or create it.
        # However, the task explicitly says "Create ... under .../code/".
        # Let's assume the script is executed from the project root (where 'code' exists).
        if (base_path / "code").exists():
            project_code_root = base_path / "code"
        else:
            project_code_root = base_path / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
            if not project_code_root.exists():
                project_code_root.mkdir(parents=True, exist_ok=True)
    
    # Define the directories to create
    directories = [
        "src",
        "tests",
        "data",
        # data subdirectories
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation",
        # src subdirectories
        "src/generation",
        "src/filtering",
        "src/training",
        "src/evaluation",
        "src/utils",
        # tests subdirectories
        "tests/unit",
        "tests/integration",
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = project_code_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nDirectory creation complete. {created_count} new directories created.")
    print(f"Base path used: {project_code_root}")

if __name__ == "__main__":
    main()
