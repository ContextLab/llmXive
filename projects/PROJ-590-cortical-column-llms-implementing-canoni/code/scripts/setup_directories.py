import os
import sys
from pathlib import Path
import yaml
import datetime

def ensure_directory_structure(root: Path) -> None:
    """
    Creates the required directory structure for the project.
    Ensures 'state/*.yaml' is NOT in .gitignore (handled in T003).
    """
    dirs = [
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
        "state"
    ]

    for d in dirs:
        path = root / d
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

def create_state_template(root: Path) -> None:
    """
    Creates a template YAML file in the state directory to ensure it is tracked.
    """
    state_dir = root / "state"
    template_path = state_dir / "template.yaml"
    
    if not template_path.exists():
        content = {
            "project": "PROJ-590-cortical-column-llms-implementing-canoni",
            "version": "0.1.0",
            "created_at": datetime.datetime.now().isoformat(),
            "artifacts": [],
            "checksums": {}
        }
        with open(template_path, "w") as f:
            yaml.dump(content, f, default_flow_style=False)
        print(f"Created state template: {template_path}")
    else:
        print(f"State template already exists: {template_path}")

def main() -> int:
    """
    Main entry point for directory setup.
    """
    root = Path(__file__).resolve().parent.parent
    print(f"Project root: {root}")
    
    ensure_directory_structure(root)
    create_state_template(root)
    
    # Verify existence
    required = [
        "src/models", "src/data", "src/training", "src/experiments", "src/utils",
        "tests/unit", "tests/integration", "scripts",
        "data/results", "data/logs", "data/configs", "state"
    ]
    
    all_exist = True
    for d in required:
        if not (root / d).is_dir():
            print(f"ERROR: Directory missing: {root / d}")
            all_exist = False
    
    if not (root / "state" / "template.yaml").exists():
        print(f"ERROR: State template missing: {root / 'state' / 'template.yaml'}")
        all_exist = False

    if all_exist:
        print("All directories and state template created successfully.")
        return 0
    else:
        print("Directory creation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())