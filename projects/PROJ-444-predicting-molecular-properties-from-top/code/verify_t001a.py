"""
Verification script for T001a.

This script verifies that all required directories and files
from task T001a have been created correctly.
"""
import sys
from pathlib import Path

def verify_t001a() -> bool:
    """
    Verify T001a deliverables.
    
    Returns:
        True if all verifications pass, False otherwise.
    """
    project_root = Path("projects/PROJ-444-predicting-molecular-properties-from-top")
    
    # Required directories
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "tests",
        "reports",
        "state",
    ]
    
    all_valid = True
    
    # Check project root
    if not project_root.exists():
        print("FAIL: Project root directory does not exist")
        return False
    
    if not project_root.is_dir():
        print("FAIL: Project root is not a directory")
        return False
    
    print(f"Project root exists: {project_root}")
    
    # Check directories
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            print(f"FAIL: Directory missing: {full_path}")
            all_valid = False
        elif not full_path.is_dir():
            print(f"FAIL: Not a directory: {full_path}")
            all_valid = False
        else:
            print(f"  OK: {full_path}")
    
    # Check README
    readme_path = project_root / "README.md"
    if not readme_path.exists():
        print("FAIL: README.md does not exist")
        all_valid = False
    else:
        content = readme_path.read_text(encoding="utf-8")
        required_text = "Project: Predicting Molecular Properties from TDA"
        if required_text not in content:
            print(f"FAIL: README.md missing required content. Content: {content}")
            all_valid = False
        elif len(content) == 0:
            print("FAIL: README.md is empty")
            all_valid = False
        else:
            print(f"  OK: README.md exists and contains required text")
    
    return all_valid

def main() -> int:
    """Main entry point."""
    print("Verifying T001a deliverables...")
    if verify_t001a():
        print("\nT001a verification PASSED")
        return 0
    else:
        print("\nT001a verification FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())