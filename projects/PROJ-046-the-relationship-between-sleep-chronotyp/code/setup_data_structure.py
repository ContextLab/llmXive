import os
import json
from pathlib import Path

def create_data_directories(project_root: str = None) -> list:
    """
    Creates the required data directory structure for the project.
    
    Returns a list of created directory paths.
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent
    
    base_path = Path(project_root)
    
    # Define the required directories relative to the project root
    # Adjusting to match the project's actual structure (data/ at root)
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "derived",
        base_path / "logs"
    ]
    
    created = []
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        created.append(str(directory))
        # Create .gitkeep files to ensure directories are tracked by git
        gitkeep = directory / ".gitkeep"
        gitkeep.touch()
    
    return created

def create_gitignore_rules(project_root: str = None) -> str:
    """
    Creates or updates the .gitignore file with rules for data and logs.
    
    Returns the path to the .gitignore file.
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent
    
    base_path = Path(project_root)
    gitignore_path = base_path / ".gitignore"
    
    # Define the rules to append
    rules = [
        "# Data directories - raw data is never committed",
        "data/raw/",
        "# Processed data - generated during analysis",
        "data/processed/",
        "# Derived data - final analysis outputs",
        "data/derived/",
        "# Logs - execution logs and error traces",
        "logs/",
        "# Ignore Python cache",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        # Ignore R specific files if not already present
        ".Rproj.user/",
        ".Rhistory",
        ".RData",
        ".Renviron",
        "renv/library/",
        "renv/activate.R",
        "renv/settings.R",
        "renv/.gitignore",
    ]
    
    # Check if file exists and read existing content
    existing_rules = set()
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing_rules = set(line.strip() for line in f if line.strip())
    
    # Determine which rules need to be added
    rules_to_add = [rule for rule in rules if rule not in existing_rules]
    
    # Append new rules
    if rules_to_add:
        with open(gitignore_path, 'a') as f:
            f.write("\n")
            for rule in rules_to_add:
                f.write(rule + "\n")
    
    return str(gitignore_path)

def create_gitkeep_files(project_root: str = None) -> list:
    """
    Creates .gitkeep files in all data and log directories to ensure they are tracked.
    
    Returns a list of created .gitkeep file paths.
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent
    
    base_path = Path(project_root)
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "derived",
        base_path / "logs"
    ]
    
    created = []
    for directory in directories:
        if directory.exists():
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
                created.append(str(gitkeep))
    return created

def main():
    """
    Main entry point to setup data structure and gitignore rules.
    """
    print("Setting up data directory structure...")
    dirs = create_data_directories()
    print(f"Created directories: {', '.join(dirs)}")
    
    print("Updating .gitignore rules...")
    gitignore = create_gitignore_rules()
    print(f"Updated .gitignore: {gitignore}")
    
    print("Creating .gitkeep files...")
    keeps = create_gitkeep_files()
    if keeps:
        print(f"Created .gitkeep files: {', '.join(keeps)}")
    else:
        print("No new .gitkeep files needed.")
    
    print("Data structure setup complete.")

if __name__ == "__main__":
    main()
