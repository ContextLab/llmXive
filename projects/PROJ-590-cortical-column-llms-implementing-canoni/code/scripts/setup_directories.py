import os
import sys
from pathlib import Path
import yaml
import datetime

def ensure_directory_structure(root: Path) -> bool:
    """
    Create the required directory structure for the project.
    Returns True if all directories were created successfully.
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
        "state",
    ]
    
    success = True
    for d in dirs:
        path = root / d
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
        except OSError as e:
            print(f"Error creating directory {path}: {e}", file=sys.stderr)
            success = False
    
    return success

def create_state_template(root: Path) -> bool:
    """
    Create the initial state template file.
    Returns True if successful.
    """
    state_dir = root / "state"
    template_path = state_dir / "template.yaml"
    
    try:
        content = {
            "project": "PROJ-590-cortical-column-llms-implementing-canoni",
            "created_at": datetime.datetime.now().isoformat(),
            "version": "0.1.0",
            "artifacts": [],
            "checksums": {}
        }
        
        with open(template_path, "w") as f:
            yaml.dump(content, f, default_flow_style=False)
        
        print(f"Created state template: {template_path}")
        return True
    except OSError as e:
        print(f"Error creating state template: {e}", file=sys.stderr)
        return False

def main():
    """Main entry point for directory setup."""
    root = Path(__file__).parent.parent
    print(f"Setting up directories in: {root}")
    
    if not ensure_directory_structure(root):
        print("Failed to create directory structure", file=sys.stderr)
        sys.exit(1)
    
    if not create_state_template(root):
        print("Failed to create state template", file=sys.stderr)
        sys.exit(1)
    
    print("Directory setup completed successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()
