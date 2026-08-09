import os
import sys
from pathlib import Path

def verify_structure():
    """
    Verify that the project directory structure exists as required by T004.
    
    Required directories:
    - code/
    - tests/
    - data/raw
    - data/processed
    - data/simulations
    - data/reports
    - docs/
    
    Returns:
        bool: True if all required directories exist, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/simulations",
        "data/reports",
        "docs"
    ]
    
    missing = []
    existing = []
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            existing.append(str(dir_path))
        else:
            missing.append(dir_name)
    
    if missing:
        print("Verification FAILED. Missing directories:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return False
    
    print("Verification PASSED. All required directories exist:")
    for d in existing:
        print(f"  {d}")
    
    # Print recursive listing as evidence
    print("\nRecursive directory listing (ls -R equivalent):")
    print(f"Project root: {project_root}")
    print("-" * 40)
    
    for root, dirs, files in os.walk(project_root):
        level = root.replace(str(project_root), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        
        sub_indent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")
    
    return True

if __name__ == "__main__":
    success = verify_structure()
    sys.exit(0 if success else 1)
