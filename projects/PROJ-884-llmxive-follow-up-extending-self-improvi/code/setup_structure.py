"""
Script to initialize the project directory structure for llmXive.
Executes the creation of directories as defined in task T001a.
"""
import os
import sys

def main():
    project_root = "projects/PROJ-884-llmxive-follow-up-extending-self-improvi"
    
    # Define the directory structure relative to the project root
    # Based on the task: mkdir -p projects/PROJ-884-llmxive-follow-up-extending-self-improvi/{data/raw,data/processed,code/{dataset,symbolic,bes,analysis,utils},tests/{unit,integration}}
    directories = [
        os.path.join(project_root, "data", "raw"),
        os.path.join(project_root, "data", "processed"),
        os.path.join(project_root, "code", "dataset"),
        os.path.join(project_root, "code", "symbolic"),
        os.path.join(project_root, "code", "bes"),
        os.path.join(project_root, "code", "analysis"),
        os.path.join(project_root, "code", "utils"),
        os.path.join(project_root, "tests", "unit"),
        os.path.join(project_root, "tests", "integration"),
    ]

    created_count = 0
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    print(f"Project structure initialization complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())