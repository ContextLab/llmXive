"""
Verify project directory structure against plan.md requirements.

This script checks for the existence of required directories:
code/, tests/, data/raw/, data/processed/, results/, state/

Outputs:
- state/structure_check.yaml with status "PASS" or "FAIL"
"""
import os
import sys
from pathlib import Path
import yaml
from datetime import datetime, timezone

# Define required directories relative to project root
REQUIRED_DIRS = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "results",
    "state"
]

def check_directory_structure():
    """Check if all required directories exist."""
    project_root = Path(__file__).parent.parent
    missing_dirs = []
    existing_dirs = []
    
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            existing_dirs.append(dir_path)
        else:
            missing_dirs.append(dir_path)
    
    return existing_dirs, missing_dirs

def write_structure_check(existing_dirs, missing_dirs):
    """Write the structure check result to state/structure_check.yaml."""
    project_root = Path(__file__).parent.parent
    output_path = project_root / "state" / "structure_check.yaml"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    status = "PASS" if not missing_dirs else "FAIL"
    
    result = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checked_directories": {
            "existing": existing_dirs,
            "missing": missing_dirs
        },
        "required_directories": REQUIRED_DIRS,
        "message": "All required directories present." if status == "PASS" 
                   else f"Missing directories: {', '.join(missing_dirs)}"
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)
    
    return result

def main():
    """Main entry point for structure verification."""
    print("Verifying project directory structure...")
    
    existing_dirs, missing_dirs = check_directory_structure()
    
    print(f"Existing directories: {len(existing_dirs)}/{len(REQUIRED_DIRS)}")
    if missing_dirs:
        print(f"Missing directories: {missing_dirs}")
    
    result = write_structure_check(existing_dirs, missing_dirs)
    
    print(f"Structure check result: {result['status']}")
    print(f"Report written to: state/structure_check.yaml")
    
    # Exit with error code if structure is invalid
    if result['status'] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
