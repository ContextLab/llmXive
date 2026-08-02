import os
import sys
from pathlib import Path
import yaml
import datetime

# Define the directory structure required by T001
# Note: The project uses 'code/' as the root for source, 'data/' for outputs, etc.
# The task description mentions 'src/', 'tests/', etc. but the existing API surface
# and project structure indicate 'code/src/', 'code/tests/', 'code/data/', 'code/scripts'.
# We will map the task requirements to the actual project tree structure.
# Task T001 requests: `src/models`, `src/data`, `src/training`, `src/experiments`, `src/utils`,
# `tests/unit`, `tests/integration`, `scripts`, `data/results`, `data/logs`, `data/configs`, `state`.
# Mapped to project root (code/):
# code/src/models, code/src/data, code/src/training, code/src/experiments, code/src/utils
# code/tests/unit, code/tests/integration
# code/scripts (already exists)
# code/data/results, code/data/logs, code/data/configs
# code/state

REQUIRED_DIRS = [
    "code/src/models",
    "code/src/data",
    "code/src/training",
    "code/src/experiments",
    "code/src/utils",
    "code/tests/unit",
    "code/tests/integration",
    "code/scripts",
    "code/data/results",
    "code/data/logs",
    "code/data/configs",
    "code/state"
]

def ensure_directory_structure():
    """Creates all required directories if they do not exist."""
    created = []
    for dir_path in REQUIRED_DIRS:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
        else:
            # Ensure it is actually a directory
            if not path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {path}")
    return created

def create_state_template():
    """Creates a template state.yaml file in code/state/ if it doesn't exist."""
    state_dir = Path("code/state")
    state_dir.mkdir(parents=True, exist_ok=True)
    template_file = state_dir / "template.yaml"
    
    if not template_file.exists():
        template_content = {
            "project": "PROJ-590-cortical-column-llms-implementing-canoni",
            "version": "0.0.1",
            "created_at": datetime.datetime.now().isoformat(),
            "artifacts": {},
            "checksums": {},
            "status": "initialized"
        }
        with open(template_file, 'w') as f:
            yaml.dump(template_content, f, default_flow_style=False)
        return str(template_file)
    return None

def main():
    """Main entry point for directory setup."""
    print("Starting directory structure setup...")
    try:
        created_dirs = ensure_directory_structure()
        if created_dirs:
            print(f"Created directories: {created_dirs}")
        else:
            print("All required directories already exist.")
        
        created_template = create_state_template()
        if created_template:
            print(f"Created state template: {created_template}")
        else:
            print("State template already exists.")
        
        print("Setup complete.")
        return 0
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
