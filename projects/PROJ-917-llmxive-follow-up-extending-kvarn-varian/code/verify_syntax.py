"""
T004: Verify Python syntax for all .py files in the project.

This script recursively finds all .py files under the 'code/' directory
and verifies their syntax using py_compile.

Exit codes:
    0: All files are syntactically valid.
    1: One or more files have syntax errors.
"""
import glob
import py_compile
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Directory '{code_dir}' does not exist.")
        sys.exit(1)

    # Find all .py files recursively
    py_files = list(code_dir.rglob("*.py"))
    
    if not py_files:
        print("No Python files found in 'code/'. Verification passed (empty).")
        sys.exit(0)

    print(f"Verifying syntax for {len(py_files)} Python files...")
    
    errors = []
    
    for file_path in py_files:
        try:
            py_compile.compile(str(file_path), doraise=True)
            print(f"  OK: {file_path.relative_to(project_root)}")
        except py_compile.PyCompileError as e:
            errors.append((file_path, str(e)))
            print(f"  FAIL: {file_path.relative_to(project_root)} - {e}")

    if errors:
        print(f"\nVerification FAILED: {len(errors)} file(s) have syntax errors.")
        sys.exit(1)
    else:
        print("\nVerification PASSED: All files are syntactically valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()
