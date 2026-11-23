import os
import sys
import json
from pathlib import Path

def verify_t001_complete():
    """
    Verify T001 completion by checking directory existence and generating
    project_structure_manifest.json.
    """
    base = Path(".")
    
    required_dirs = {
        "src": ["data", "analysis", "viz", "utils"],
        "tests": ["unit", "integration", "contract"],
        "data": ["raw", "processed"],
        "output": ["results", "figures"],
        "logs": []
    }
    
    manifest = {}
    all_exist = True
    
    for top_dir, sub_dirs in required_dirs.items():
        top_path = base / top_dir
        if not top_path.is_dir():
            print(f"MISSING: {top_path}")
            all_exist = False
            manifest[top_dir] = []
            continue
        
        # Verify subdirectories
        existing_subs = []
        for sub in sub_dirs:
            sub_path = top_path / sub
            if sub_path.is_dir():
                existing_subs.append(sub)
            else:
                print(f"MISSING SUBDIR: {sub_path}")
                all_exist = False
        
        manifest[top_dir] = existing_subs
    
    if all_exist:
        # Write the manifest
        manifest_path = base / "project_structure_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"SUCCESS: All directories exist. Manifest written to {manifest_path}")
        return True
    else:
        print("FAILURE: Some directories are missing.")
        return False

def main():
    success = verify_t001_complete()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()