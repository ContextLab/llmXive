"""
Verification script for T001b: Initialize Python packages.

This script ensures that __init__.py files exist in all required package directories
and that the 'code' package is importable.
"""
import os
import sys
import subprocess

def main():
    # Define the required package directories relative to the project root
    # Assuming the script is run from the project root or code/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    packages = [
        "code",
        "tests",
        "code/utils",
        "code/models"
    ]
    
    missing_init = []
    
    for pkg in packages:
        init_path = os.path.join(project_root, pkg, "__init__.py")
        if not os.path.isfile(init_path):
            missing_init.append(init_path)
    
    if missing_init:
        print("ERROR: Missing __init__.py files in the following packages:", file=sys.stderr)
        for path in missing_init:
            print(f"  - {path}", file=sys.stderr)
        sys.exit(1)
    
    # Change to project root to ensure import works correctly
    os.chdir(project_root)
    
    # Verify importability
    try:
        # Attempt to import the code package
        import code
        print("SUCCESS: 'code' package imported successfully.")
        
        # Optional: Verify sub-packages if they are intended to be top-level imports
        # Note: code/utils and code/models are sub-packages, usually imported as code.utils
        # The task specifically asks to verify `import code`
    except ImportError as e:
        print(f"ERROR: Failed to import 'code' package: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("Verification passed: All required __init__.py files exist and 'code' is importable.")
    return 0

if __name__ == "__main__":
    sys.exit(main())