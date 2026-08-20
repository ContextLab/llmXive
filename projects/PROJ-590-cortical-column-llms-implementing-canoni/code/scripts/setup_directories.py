import os
import sys
from pathlib import Path
import yaml
import datetime

def ensure_directory_structure(root: Path) -> None:
    """
    Create the required directory structure for the project.
    Ensures tests/unit, tests/integration, scripts, data/results,
    data/logs, data/configs, and state/ exist.
    """
    dirs_to_create = [
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "scripts",
        root / "data" / "results",
        root / "data" / "logs",
        root / "data" / "configs",
        root / "state",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        # Ensure __init__.py exists in test directories if not already
        if "tests" in str(dir_path) and dir_path.is_dir():
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

def create_state_template(root: Path) -> None:
    """
    Create a template state file in the state/ directory.
    This file serves as a baseline for experiment versioning.
    """
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    template_path = state_dir / "template.yaml"

    template_content = {
        "experiment_id": "template",
        "created_at": datetime.datetime.now().isoformat(),
        "version": "0.0.1",
        "parameters": {},
        "metrics": {},
        "status": "initialized",
        "notes": "Template state file for experiment tracking."
    }

    with open(template_path, "w") as f:
        yaml.dump(template_content, f, default_flow_style=False)

def ensure_init_files(root: Path) -> None:
    """
    Ensure __init__.py files exist in all required directories.
    """
    dirs = [
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "scripts",
        root / "data" / "results",
        root / "data" / "logs",
        root / "data" / "configs",
        root / "state",
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()

def create_gitignore(root: Path) -> None:
    """
    Create or update .gitignore to ensure state files are tracked.
    Explicitly excludes data/, __pycache__, *.pyc, *.log
    but explicitly includes data/configs, data/results, data/logs, and state/.
    """
    gitignore_path = root / ".gitignore"
    
    # Read existing content if present
    existing_content = ""
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            existing_content = f.read()
    
    # Define required patterns
    ignore_patterns = [
        "# Python",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "build/",
        "develop-eggs/",
        "dist/",
        "downloads/",
        "eggs/",
        ".eggs/",
        "lib/",
        "lib64/",
        "parts/",
        "sdist/",
        "var/",
        "wheels/",
        "*.egg-info/",
        ".installed.cfg",
        "*.egg",
        "",
        "# Project specific data",
        "data/",
        "!data/configs/",
        "!data/results/",
        "!data/logs/",
        "data/logs/*.log",
        "",
        "# State tracking - MUST NOT be ignored",
        "state/",
        "!state/*.yaml",
        "!state/*.json",
        "",
        "# Virtual environments",
        "venv/",
        "ENV/",
        "env/",
        ".env",
        "",
        "# IDE",
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        "",
        "# OS",
        ".DS_Store",
        "Thumbs.db",
    ]
    
    new_content = "\n".join(ignore_patterns) + "\n"
    
    # Only write if content changed or file doesn't exist
    if not gitignore_path.exists() or existing_content != new_content:
        with open(gitignore_path, "w") as f:
            f.write(new_content)

def main():
    """
    Main entry point for directory setup.
    Creates all required directories and configuration files.
    """
    # Determine project root (assuming code/scripts is current dir)
    current_dir = Path(__file__).resolve()
    project_root = current_dir.parent.parent
    
    print(f"Setting up directory structure at: {project_root}")
    
    # Create directories
    ensure_directory_structure(project_root)
    
    # Create state template
    create_state_template(project_root)
    
    # Ensure __init__.py files
    ensure_init_files(project_root)
    
    # Create/update .gitignore
    create_gitignore(project_root)
    
    print("Directory structure setup complete.")
    print("Created directories: tests/unit, tests/integration, scripts, data/results, data/logs, data/configs, state/")
    print("Created: state/template.yaml")
    print("Updated: .gitignore (ensuring state/*.yaml is tracked)")

if __name__ == "__main__":
    main()
