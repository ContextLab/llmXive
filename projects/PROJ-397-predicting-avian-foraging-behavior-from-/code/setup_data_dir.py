import os
import sys
from pathlib import Path

def main():
    """
    Initialize the data/ directory for the project.
    Creates the directory structure and a .gitkeep file to ensure
    the directory is tracked by git.
    """
    # Determine project root based on the task description
    # The task specifies: projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/
    # However, standard project structure implies 'code' is the root for this repo context.
    # We will create the path relative to the current working directory or a fixed prefix
    # if the environment dictates a specific project root.
    
    # Based on the API surface provided (e.g., code/setup_viz_dir.py imports from utils.config),
    # we assume the execution context is inside the 'code' directory or the root.
    # The task explicitly asks for: projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/
    
    # To be safe and consistent with the "whole project tree" constraint, 
    # we will construct the path relative to the current working directory.
    # If the runner executes this from the project root, we create the nested path.
    
    project_root = Path.cwd()
    target_dir = project_root / "projects" / "PROJ-397-predicting-avian-foraging-behavior-from-" / "code" / "data"
    
    # If the runner is already inside the project root (e.g. 'code' directory), 
    # we check if the path exists. If the prompt implies the project root IS the 
    # 'projects/.../code' directory, we adjust. 
    # Given the rejected tasks mentioned "projects/.../code/data/", we strictly follow that path.
    
    # Ensure the directory exists
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep file
    gitkeep_file = target_dir / ".gitkeep"
    gitkeep_file.touch(exist_ok=True)
    
    print(f"Successfully created directory: {target_dir}")
    print(f"Successfully created .gitkeep file: {gitkeep_file}")

if __name__ == "__main__":
    main()