"""
Script to create the required directory structure for the project.
Ensures all directories specified in plan.md exist.
"""
import os
import sys
from pathlib import Path
import yaml
import datetime

def ensure_directory_structure(root_path: Path) -> None:
    """
    Creates the required directory tree as per plan.md.
    
    Required directories:
    - src/models, src/data, src/training, src/experiments, src/utils
    - tests/unit, tests/integration
    - scripts
    - data/results, data/logs, data/configs
    - state
    """
    required_dirs = [
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "scripts",
        "data/results",
        "data/logs",
        "data/configs",
        "state",
        # Additional directories from T001b and T001c context
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/unit/models",
        "tests/unit/data",
    ]

    for dir_path in required_dirs:
        full_path = root_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_state_template(root_path: Path) -> None:
    """
    Creates the initial state/template.yaml file if it doesn't exist.
    This satisfies T001f requirement for artifact versioning.
    """
    template_path = root_path / "state" / "template.yaml"
    
    if template_path.exists():
        print(f"State template already exists at {template_path}")
        return

    template_content = {
        "hashes": {},
        "artifacts": {},
        "updated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    with open(template_path, 'w') as f:
        yaml.dump(template_content, f, default_flow_style=False, sort_keys=False)
    
    print(f"Created state template: {template_path}")

def main():
    """Main entry point for directory setup."""
    # Determine project root (parent of scripts directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    print(f"Project root: {project_root}")
    
    ensure_directory_structure(project_root)
    create_state_template(project_root)
    
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()
