"""
Script to initialize the project directory structure for PROJ-061.
This implements task T009.
"""
import os
import sys

def create_directories():
    """Create the required directory structure."""
    # Define the base directory (project root)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the directories to create based on tasks.md and T009
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        # T001 also mentioned docs, though T009 specifically lists these
        "docs"
    ]

    created = []
    failed = []

    for dir_path in dirs_to_create:
        full_path = os.path.join(base_dir, dir_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        except Exception as e:
            failed.append((dir_path, str(e)))
            print(f"Error creating {dir_path}: {e}", file=sys.stderr)

    # Ensure __init__.py files exist in Python packages
    init_dirs = ["code", "tests", "tests/unit", "tests/integration", "tests/contract"]
    for pkg_dir in init_dirs:
        init_path = os.path.join(base_dir, pkg_dir, "__init__.py")
        if not os.path.exists(init_path):
            try:
                with open(init_path, "w") as f:
                    f.write(f'"""\n{pkg_dir.replace("/", ".")} package.\n"""\n')
                print(f"Created __init__.py: {pkg_dir}/__init__.py")
            except Exception as e:
                failed.append((f"{pkg_dir}/__init__.py", str(e)))
                print(f"Error creating __init__.py for {pkg_dir}: {e}", file=sys.stderr)
        else:
            print(f"__init__.py already exists: {pkg_dir}/__init__.py")

    if failed:
        print(f"\nSummary: {len(created)} directories created, {len(failed)} failed.")
        return False
    else:
        print(f"\nSuccess: All directories and init files created.")
        return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)