"""
Script to initialize project directory structure for llmXive.
Creates directories matching the plan.md structure.
"""
import os
from pathlib import Path

# Define the project root relative to this script's location (project root)
# Since this script is in code/, we go up one level to get the project root
project_root = Path(__file__).resolve().parent.parent

# Directories to create based on tasks.md T001
directories = [
    "data/raw",
    "data/processed",
    "code/utils",
    "tests",
    "results/paper_figures"
]

def main():
    print(f"Initializing project structure at: {project_root}")
    created_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()
