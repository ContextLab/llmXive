"""
Data Structure Setup Utilities for PROJ-046

Creates the necessary directory structure and .gitignore rules
for the project's data and logs.
"""
import os
import json
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    # Assuming this file is in code/ directory
    return current_file.parent.parent


def create_data_directories() -> None:
    """Create the standard data directory structure."""
    root = get_project_root()
    
    directories = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "derived",
        root / "logs",
        root / "figures",
        root / "reports"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked by git
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Keep this directory\n", encoding="utf-8")
    
    print(f"Created {len(directories)} directories.")


def create_gitignore_rules() -> None:
    """Create or update .gitignore rules for data and logs."""
    root = get_project_root()
    gitignore_path = root / ".gitignore"
    
    rules = [
        "# Data directories - ignore raw data and large derived files",
        "data/raw/*",
        "!data/raw/.gitkeep",
        "data/processed/*",
        "!data/processed/.gitkeep",
        "data/derived/*",
        "!data/derived/.gitkeep",
        "",
        "# Logs directory",
        "logs/*",
        "!logs/.gitkeep",
        "",
        "# Figures and Reports",
        "figures/*",
        "!figures/.gitkeep",
        "reports/*",
        "!reports/.gitkeep",
        "",
        "# Python cache",
        "__pycache__/",
        "*.py[cod]",
        "$py.class",
        "",
        "# R artifacts",
        "*.RData",
        "*.rds",
        ".Rhistory",
        "renv/",
        "!renv/activate.R",
        "!renv/settings.json",
        "!renv/activate"
    ]
    
    existing_rules = set()
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        existing_rules = set(line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#"))
    
    new_rules_added = False
    with open(gitignore_path, "a", encoding="utf-8") as f:
        for rule in rules:
            if rule.strip() and not rule.startswith("#"):
                # Check if rule already exists (ignoring case and whitespace)
                clean_rule = rule.strip()
                if clean_rule not in existing_rules:
                    f.write(rule + "\n")
                    new_rules_added = True
            else:
                f.write(rule + "\n")
    
    if new_rules_added:
        print("Updated .gitignore with data and log rules.")
    else:
        print(".gitignore already contains necessary rules.")


def create_gitkeep_files() -> None:
    """Ensure .gitkeep files exist in all data directories."""
    root = get_project_root()
    
    directories = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "derived",
        root / "logs",
        root / "figures",
        root / "reports"
    ]
    
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Keep this directory\n", encoding="utf-8")
            print(f"Created .gitkeep in {directory}")


def main() -> None:
    """Main entry point to set up data structure."""
    print("Setting up data directory structure...")
    create_data_directories()
    create_gitkeep_files()
    create_gitignore_rules()
    print("Data structure setup complete.")


if __name__ == "__main__":
    main()