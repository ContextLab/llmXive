import os
import sys
import json
from pathlib import Path

def main():
    """
    Create project structure per implementation plan.
    Creates directories: code/, data/, tests/, state/, models/, data/raw/, data/processed/, reports/
    Outputs state/structure_manifest.json verifying existence of all directories.
    """
    # Define the required directories relative to the project root
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

    project_root = Path.cwd()
    created_dirs = []
    failed_dirs = []

    print(f"Creating project structure in: {project_root}")

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"  Created/Verified: {full_path}")
        except OSError as e:
            failed_dirs.append({"path": dir_path, "error": str(e)})
            print(f"  Failed to create: {full_path} - {e}")

    # Generate the manifest
    manifest = {
        "project_root": str(project_root),
        "timestamp": str(Path(project_root).stat(st_mtime=None) if False else None), # Simplified timestamp logic or use datetime
        "created_directories": created_dirs,
        "failed_directories": failed_dirs,
        "total_requested": len(required_dirs),
        "total_created": len(created_dirs),
        "status": "success" if not failed_dirs else "partial_failure"
    }

    # Add actual timestamp
    from datetime import datetime
    manifest["timestamp"] = datetime.now().isoformat()

    manifest_path = project_root / "state" / "structure_manifest.json"
    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Manifest written to: {manifest_path}")
    except Exception as e:
        print(f"Error writing manifest: {e}")
        sys.exit(1)

    if failed_dirs:
        print("Warning: Some directories could not be created.")
        sys.exit(1)
    
    print("Project structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main() if main() is not None else 0)
