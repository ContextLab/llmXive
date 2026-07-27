import os
import sys
from pathlib import Path
import yaml
import datetime

def ensure_directory_structure():
    """
    Creates the explicit directory tree required by plan.md and Constitution Principle V.
    Returns the list of created paths for verification.
    """
    # Define relative paths based on project root
    # The script is expected to be run from the project root or code/ directory
    # We will assume the script is run from the project root for clarity,
    # but handle relative to script location if needed.
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
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

    created_paths = []
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path {full_path} exists but is not a directory.")
    
    return created_paths

def create_state_template():
    """
    Creates the template YAML file in state/ as required by Constitution Principle V.
    Keys: hashes, artifacts, updated_at.
    """
    project_root = Path(__file__).resolve().parent.parent
    state_dir = project_root / "state"
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    template_file = state_dir / "project_state.yaml"
    
    if template_file.exists():
        # Optional: update timestamp if file exists but content is stale
        # For this task, we ensure it exists with the correct structure.
        # We overwrite to ensure the schema is correct.
        pass

    template_content = {
        "hashes": {},
        "artifacts": [],
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    with open(template_file, 'w') as f:
        yaml.dump(template_content, f, default_flow_style=False, sort_keys=False)
    
    return str(template_file)

def main():
    print("Setting up project directory structure...")
    
    try:
        created_dirs = ensure_directory_structure()
        print(f"Created {len(created_dirs)} directories:")
        for d in created_dirs:
            print(f"  - {d}")
        
        template_path = create_state_template()
        print(f"Created state template: {template_path}")
        
        # Print a summary for the verifier
        print("\nDirectory Structure Verification:")
        project_root = Path(__file__).resolve().parent.parent
        required_dirs = [
            "src/models", "src/data", "src/training", "src/experiments", "src/utils",
            "tests/unit", "tests/integration", "scripts",
            "data/results", "data/logs", "data/configs", "state"
        ]
        
        all_exist = True
        for d in required_dirs:
            p = project_root / d
            exists = p.exists() and p.is_dir()
            status = "OK" if exists else "MISSING"
            print(f"  [{status}] {d}")
            if not exists:
                all_exist = False
        
        if all_exist:
            print("\n✅ All required directories and state template created successfully.")
            return 0
        else:
            print("\n❌ Some directories failed to create.")
            return 1
            
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
