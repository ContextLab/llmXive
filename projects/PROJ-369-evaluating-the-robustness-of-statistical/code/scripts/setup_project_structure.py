import os
import sys
from pathlib import Path
import json
from datetime import datetime
from src.utils.config import get_path, ensure_dirs

def main():
    """
    T001: Create project structure and generate state/structure_manifest.json.
    
    Creates the following directories:
    - src/, src/data/, src/synthesis/, src/analysis/, src/viz/, src/utils/
    - tests/unit/, tests/integration/, tests/contract/
    - data/raw/, data/processed/, data/results/
    - specs/, state/
    
    Outputs:
    - state/structure_manifest.json: JSON file listing all created paths.
    """
    # Define required directories relative to project root
    required_dirs = [
        "src",
        "src/data",
        "src/synthesis",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
        "state"
    ]

    project_root = get_path()
    created_paths = []
    errors = []

    print(f"Creating project structure at: {project_root}")

    for dir_path in required_dirs:
        full_path = Path(project_root) / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                created_paths.append(str(full_path))
                print(f"  Created: {full_path}")
            else:
                created_paths.append(str(full_path))
                print(f"  Exists:  {full_path}")
        except Exception as e:
            error_msg = f"Failed to create {full_path}: {str(e)}"
            errors.append(error_msg)
            print(f"  ERROR:   {error_msg}")

    # Generate manifest
    manifest = {
        "created_at": datetime.now().isoformat(),
        "project_root": str(project_root),
        "directories_created": created_paths,
        "total_count": len(created_paths),
        "errors": errors,
        "status": "success" if not errors else "partial_failure"
    }

    manifest_path = Path(project_root) / "state" / "structure_manifest.json"
    ensure_dirs([str(Path(project_root) / "state")])
    
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        print(f"\nManifest written to: {manifest_path}")
    except Exception as e:
        print(f"ERROR: Failed to write manifest: {str(e)}")
        sys.exit(1)

    if errors:
        print(f"\nCompleted with {len(errors)} errors.")
        sys.exit(1)
    else:
        print("\nProject structure creation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
