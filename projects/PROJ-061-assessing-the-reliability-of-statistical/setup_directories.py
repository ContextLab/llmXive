"""
Script to ensure the required directory structure for the project exists.
This satisfies task T009: Setup directory structure.
"""
import os
import sys

# Define the required directories relative to the project root
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "code",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def main():
    """Create missing directories and __init__.py files."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure we are running from the project root or adjust paths if needed
    # Assuming this script is at the root as per task description
    
    created_count = 0
    
    for dir_path in REQUIRED_DIRS:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
        
        # Ensure __init__.py exists in Python packages
        if dir_path.startswith("code") or dir_path.startswith("tests"):
            init_file = os.path.join(full_path, "__init__.py")
            if not os.path.exists(init_file):
                # Create a minimal __init__.py
                with open(init_file, "w") as f:
                    f.write('"""\nAuto-generated init file for package.\n"""\n')
                print(f"Created __init__.py: {init_file}")
            else:
                print(f"__init__.py exists: {init_file}")

    print(f"\nDirectory structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())