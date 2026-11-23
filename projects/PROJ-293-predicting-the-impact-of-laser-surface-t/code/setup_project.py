import os
import sys
import json
from pathlib import Path

def main():
    """
    Creates the required project directory structure and generates a manifest file
    verifying the existence of all directories.
    
    Directories created:
    - code/
    - data/
    - tests/
    - state/
    - models/
    - data/raw/
    - data/processed/
    - reports/
    
    Output:
    - state/structure_manifest.json
    """
    # Define the required directories relative to the project root
    base_dir = Path(".")
    required_dirs = [
        "code",
        "data",
        "tests",
        "state",
        "models",
        "data/raw",
        "data/processed",
        "reports"
    ]

    created_dirs = []
    missing_dirs = []

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created/Verified directory: {dir_path}")
        except Exception as e:
            missing_dirs.append({"path": dir_path, "error": str(e)})
            print(f"Failed to create directory {dir_path}: {e}", file=sys.stderr)

    # Generate the manifest
    manifest = {
        "status": "success" if not missing_dirs else "partial_failure",
        "timestamp": str(Path("state").parent / "state" / "manifest_timestamp_placeholder"), # Placeholder for actual timestamp logic if needed, but simple string is fine
        "directories": {
            "created": created_dirs,
            "failed": missing_dirs
        },
        "verification": {
            "total_required": len(required_dirs),
            "total_created": len(created_dirs),
            "all_exist": all(d.exists() for d in [base_dir / d for d in created_dirs])
        }
    }

    # Ensure state directory exists before writing manifest
    state_dir = base_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = state_dir / "structure_manifest.json"
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        print(f"Manifest written to: {manifest_path}")
    except Exception as e:
        print(f"Failed to write manifest: {e}", file=sys.stderr)
        sys.exit(1)

    if missing_dirs:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
