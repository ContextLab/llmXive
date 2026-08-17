"""
Script to create the project directory structure.
This ensures all required directories exist before running other tasks.
"""
import os
import sys

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    structure = [
        "code",
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "code/output",
        "tests",
        "data",
        "artifacts",
        "figures",
        "specs"
    ]

    created = []
    for rel_path in structure:
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created.append(rel_path)
            print(f"Created: {rel_path}")
        else:
            print(f"Exists:  {rel_path}")

    if not created:
        print("All directories already exist.")
    else:
        print(f"\nSuccessfully created {len(created)} directories.")

    # Verify __init__.py files exist or create placeholders if missing
    init_dirs = ["code", "code/data", "code/models", "code/analysis", "code/utils", "tests"]
    for d in init_dirs:
        init_file = os.path.join(base_dir, d, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write('"""\n' + d + "\n""\n")
            print(f"Created: {d}/__init__.py")

if __name__ == "__main__":
    main()