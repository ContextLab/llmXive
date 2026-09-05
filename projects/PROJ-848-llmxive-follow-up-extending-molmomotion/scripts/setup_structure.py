"""
Script to initialize the project directory structure for T001a.
Run this to ensure all required folders exist.
"""
import os
import sys

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_name = os.path.basename(base_dir)
    
    # Define the structure to create
    # We are inside scripts/, so base_dir is the project root
    structure = [
        "code/src",
        "code/tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/001-llmxive-motion-scaling/contracts",
        "state",
        "figures",
    ]

    created_count = 0
    for path in structure:
        full_path = os.path.join(base_dir, path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    
    # Create __init__.py files if they don't exist to ensure packages are recognized
    init_paths = [
        os.path.join(base_dir, "code"),
        os.path.join(base_dir, "data"),
        os.path.join(base_dir, "specs"),
        os.path.join(base_dir, "state"),
        os.path.join(base_dir, "code", "src"),
        os.path.join(base_dir, "code", "tests"),
        os.path.join(base_dir, "code", "tests", "integration"),
    ]

    for p in init_paths:
        init_file = os.path.join(p, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f"# Auto-generated for {project_name}\n")
            print(f"Created __init__.py: {init_file}")

    print(f"\nSetup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
