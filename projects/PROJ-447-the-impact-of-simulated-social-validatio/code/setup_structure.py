"""
Script to create the detailed directory structure for the project.
This satisfies Task T004.
"""
import os
import sys

def create_directories():
    """Create the required directory structure."""
    # Define relative paths based on project root
    base_paths = [
        "code/data",
        "code/analysis",
        "code/viz",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
    ]

    created = []
    skipped = []

    for path in base_paths:
        if os.path.exists(path):
            skipped.append(path)
            continue
        
        os.makedirs(path, exist_ok=True)
        created.append(path)
        
        # Create __init__.py files for Python packages
        if path.startswith("code") or path.startswith("tests"):
            init_path = os.path.join(path, "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, "w") as f:
                    f.write(f"# Package: {path}\n")
                created.append(init_path)

    print(f"Created directories: {len(created)}")
    if skipped:
        print(f"Skipped existing directories: {skipped}")
    
    return len(created) > 0

if __name__ == "__main__":
    print("Setting up project directory structure...")
    success = create_directories()
    if success:
        print("Directory structure setup complete.")
        sys.exit(0)
    else:
        print("No new directories created (all exist).")
        sys.exit(0)