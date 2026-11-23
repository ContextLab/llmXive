"""
Project initialization script for llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information".

This script creates the required directory structure as per the implementation plan.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the current working directory
    # The task specifies the structure relative to the project root
    project_root = Path("projects/PROJ-933-llmxive-followup-extending-anti-self-di")
    
    # Define the directories to create based on the task description
    directories = [
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "analysis",
        project_root / "code" / "config",
        project_root / "data",
        project_root / "results",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nProject structure initialized. Created {created_count} new directories.")
    print(f"Project root: {project_root.resolve()}")

if __name__ == "__main__":
    main()