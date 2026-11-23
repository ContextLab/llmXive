"""
Setup script for llmXive follow-up project structure.
Creates the directory tree defined in T001.
"""
import os
from pathlib import Path

def main():
    # Project root relative to where this script is run
    # The task specifies paths relative to the project root.
    # We assume this script is run from the repository root or the project root.
    # To be safe, we define the base as the current working directory.
    base = Path.cwd()

    # Define the directory structure as per T001
    # Path: projects/PROJ-933-llmxive-followup-extending-anti-self-di/
    project_root = base / "projects" / "PROJ-933-llmxive-followup-extending-anti-self-di"
    
    # Subdirectories
    code_data = project_root / "code" / "data"
    code_models = project_root / "code" / "models"
    code_analysis = project_root / "code" / "analysis"
    code_config = project_root / "code" / "config"
    
    data_dir = project_root / "data"
    results_dir = project_root / "results"

    directories = [
        code_data,
        code_models,
        code_analysis,
        code_config,
        data_dir,
        results_dir,
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory.relative_to(base)}")
            created_count += 1
        else:
            print(f"Directory exists: {directory.relative_to(base)}")

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

if __name__ == "__main__":
    main()