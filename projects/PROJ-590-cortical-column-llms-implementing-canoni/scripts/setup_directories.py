"""
Script to create the required directory structure for the project.
Also creates the state template YAML file as required by Constitution Principle V.
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Define the required directory tree relative to the project root
REQUIRED_DIRS = [
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

def create_directories():
    """Create all required directories if they do not exist."""
    project_root = Path(__file__).resolve().parent.parent
    created = []
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path.relative_to(project_root)))
            print(f"Created directory: {full_path.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {full_path.relative_to(project_root)}")
    
    if not created:
        print("All required directories already exist.")
    else:
        print(f"Created {len(created)} new directories.")
    
    return project_root

def create_state_template(project_root):
    """
    Create the state template YAML file with required keys:
    hashes, artifacts, updated_at
    """
    state_dir = project_root / "state"
    template_file = state_dir / "project_state.yaml"
    
    # Prepare the initial state content
    initial_state = {
        "hashes": {},
        "artifacts": [],
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # Write as YAML (using simple formatting to avoid external deps if possible, 
    # but since we are in a Python script, we can use a simple manual dump or PyYAML if available)
    # To ensure robustness without assuming PyYAML is installed yet, we write manually.
    # However, the task requires a YAML file. Let's try to import yaml, fallback to manual.
    
    try:
        import yaml
        with open(template_file, "w") as f:
            yaml.dump(initial_state, f, default_flow_style=False, sort_keys=False)
        print(f"Created state template: {template_file.relative_to(project_root)}")
    except ImportError:
        # Fallback: write manually formatted YAML
        with open(template_file, "w") as f:
            f.write("hashes: {}\n")
            f.write("artifacts: []\n")
            f.write(f"updated_at: {initial_state['updated_at']}\n")
        print(f"Created state template (manual YAML): {template_file.relative_to(project_root)}")

def main():
    print("Setting up project directory structure...")
    project_root = create_directories()
    create_state_template(project_root)
    print("Directory setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
