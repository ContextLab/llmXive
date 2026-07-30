import os
import sys
from pathlib import Path
import yaml
import datetime

def ensure_directory_structure(root: Path) -> None:
    """
    Create the required directory tree for data hygiene and project structure.
    
    Creates:
    - data/raw: For raw, unprocessed data downloads
    - data/processed: For cleaned, transformed data ready for modeling
    - data/interim: For intermediate data states during processing
    - src/ subdirectories (models, data, training, experiments, utils)
    - tests/ subdirectories (unit, integration)
    - scripts/
    - data/results, data/logs, data/configs
    - state/
    """
    directories = [
        "data/raw",
        "data/processed",
        "data/interim",
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
    ]
    
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_state_template(root: Path) -> None:
    """
    Create the initial state/template.yaml file if it doesn't exist.
    
    Schema: {"hashes": {}, "artifacts": {}, "updated_at": "YYYY-MM-DDTHH:MM:SSZ"}
    """
    template_path = root / "state" / "template.yaml"
    
    if template_path.exists():
        print(f"State template already exists at {template_path}")
        return
    
    template_content = {
        "hashes": {},
        "artifacts": {},
        "updated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    with open(template_path, 'w') as f:
        yaml.dump(template_content, f, default_flow_style=False)
    
    print(f"Created state template at {template_path}")

def main() -> None:
    """Main entry point for directory setup."""
    # Determine project root (assume script is in code/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    print(f"Project root: {project_root}")
    
    ensure_directory_structure(project_root)
    create_state_template(project_root)
    
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()
