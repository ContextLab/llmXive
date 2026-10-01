import os
import sys
import json
from pathlib import Path

def main():
    """
    Creates the project directory structure and generates a manifest verifying existence.
    """
    # Define the required directories relative to the project root
    base_dirs = [
        "code",
        "data",
        "tests",
        "state",
        "reports",
        "models",
        "data/raw",
        "data/processed"
    ]

    project_root = Path(".")
  
    created_dirs = []
    missing_dirs = []

    for dir_name in base_dirs:
        full_path = project_root / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        except OSError as e:
            missing_dirs.append({"path": str(full_path), "error": str(e)})

    # Generate the manifest
    manifest = {
        "status": "success" if not missing_dirs else "partial_failure",
        "created_directories": created_dirs,
        "failed_directories": missing_dirs,
        "total_created": len(created_dirs),
        "total_failed": len(missing_dirs)
    }

    manifest_path = project_root / "state" / "structure_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Project structure created. Manifest written to {manifest_path}")
    print(f"Directories created: {len(created_dirs)}")
    
    if missing_dirs:
        print(f"Failed to create: {len(missing_dirs)}")
        for m in missing_dirs:
            print(f"  - {m['path']}: {m['error']}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
