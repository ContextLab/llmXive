"""
Script to initialize the project structure for PROJ-192.
Creates necessary directories: src/, tests/, data/, results/, and subdirectories
as defined in the implementation plan.
"""
import os
import sys

def create_structure():
    root = os.getcwd()
    
    # Define all required directories
    directories = [
        # Source code structure
        os.path.join(root, "src"),
        os.path.join(root, "src", "models"),
        os.path.join(root, "src", "utils"),
        os.path.join(root, "src", "pipelines"),
        os.path.join(root, "src", "cli"),
        os.path.join(root, "src", "config"),
        
        # Tests structure
        os.path.join(root, "tests"),
        os.path.join(root, "tests", "unit"),
        os.path.join(root, "tests", "integration"),
        os.path.join(root, "tests", "contract"),
        
        # Data structure
        os.path.join(root, "data"),
        os.path.join(root, "data", "raw-seq"),
        os.path.join(root, "data", "qc"),
        os.path.join(root, "data", "metadata"),
        os.path.join(root, "data", "cleaned"),
        
        # Results structure
        os.path.join(root, "results"),
        os.path.join(root, "results", "figures"),
        
        # Specs (feature directory)
        os.path.join(root, "specs"),
        os.path.join(root, "specs", "001-impact-of-environmental-factors"),
        
        # Docs
        os.path.join(root, "docs"),
    ]

    created = 0
    skipped = 0

    for directory in directories:
        if os.path.exists(directory):
            skipped += 1
            continue
        try:
            os.makedirs(directory)
            print(f"Created: {directory}")
            created += 1
        except OSError as e:
            print(f"Error creating {directory}: {e}", file=sys.stderr)
            return 1

    print(f"\nProject structure initialization complete.")
    print(f"Created {created} directories, skipped {skipped} existing.")
    return 0

if __name__ == "__main__":
    sys.exit(create_structure())