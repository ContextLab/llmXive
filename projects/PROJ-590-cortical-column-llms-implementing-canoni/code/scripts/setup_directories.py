import os
import sys
from pathlib import Path
import yaml
import datetime

def ensure_directory_structure(root_dir: str) -> None:
    """
    Create the explicit directory tree required by plan.md and Constitution Principle V.
    Creates:
      src/models, src/data, src/training, src/experiments, src/utils
      tests/unit, tests/integration
      scripts
      data/results, data/logs, data/configs
      state
    """
    root = Path(root_dir)
    
    # Core source directories
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
    
    created = []
    for d in dirs:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
        elif not path.is_dir():
            raise RuntimeError(f"Path exists but is not a directory: {path}")
    
    if created:
        print(f"Created {len(created)} directories:")
        for c in created:
            print(f"  {c}")
    else:
        print("All required directories already exist.")

def create_state_template(root_dir: str) -> None:
    """
    Create state/template.yaml with keys: hashes, artifacts, updated_at
    as required by Constitution Principle V.
    """
    root = Path(root_dir)
    template_path = root / "state" / "template.yaml"
    
    if template_path.exists():
        print(f"Template already exists at {template_path}, skipping creation.")
        return

    template_data = {
        "hashes": {},
        "artifacts": [],
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    with open(template_path, "w", encoding="utf-8") as f:
        yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Created state template at {template_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/setup_directories.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    ensure_directory_structure(project_root)
    create_state_template(project_root)
    print("Directory setup complete.")

if __name__ == "__main__":
    main()
