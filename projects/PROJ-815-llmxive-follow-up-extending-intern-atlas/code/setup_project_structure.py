"""
Project structure setup script for PROJ-815-llmxive-follow-up-extending-intern-atlas.
Creates the required directory hierarchy for code, data, tests, and specs.
"""
import os
import sys

PROJECT_ROOT = "projects/PROJ-815-llmxive-follow-up-extending-intern-atlas"

DIRECTORIES = [
    # Code structure
    os.path.join(PROJECT_ROOT, "code", "data"),
    os.path.join(PROJECT_ROOT, "code", "models"),
    os.path.join(PROJECT_ROOT, "code", "analysis"),
    os.path.join(PROJECT_ROOT, "code", "utils"),
    
    # Data structure
    os.path.join(PROJECT_ROOT, "data", "raw"),
    os.path.join(PROJECT_ROOT, "data", "processed"),
    
    # Test structure
    os.path.join(PROJECT_ROOT, "tests", "unit"),
    os.path.join(PROJECT_ROOT, "tests", "integration"),
    
    # Ensure root exists
    PROJECT_ROOT,
]

def main():
    created_count = 0
    skipped_count = 0
    
    print(f"Setting up project structure in: {PROJECT_ROOT}")
    
    for dir_path in DIRECTORIES:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created: {dir_path}")
            created_count += 1
        else:
            skipped_count += 1
            
    print(f"\nSetup complete.")
    print(f"  New directories: {created_count}")
    print(f"  Existing directories: {skipped_count}")
    
    # Verify structure
    missing = [d for d in DIRECTORIES if not os.path.exists(d)]
    if missing:
        print(f"ERROR: Failed to create the following directories: {missing}")
        sys.exit(1)
        
    print("All directories verified successfully.")

if __name__ == "__main__":
    main()