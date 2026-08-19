"""
Script to initialize the llmXive project directory structure.
Creates all required directories for the research pipeline.
"""
import os
import sys

REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "code/lib",
    "code/data",
    "code/models",
    "code/evaluation",
    "data/results",
    "data/logs",
    "data/intermediate",
]

def create_directories():
    """Create all required directories if they do not exist."""
    root = os.getcwd()
    created = []
    skipped = []

    for dir_path in REQUIRED_DIRS:
        full_path = os.path.join(root, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            created.append(dir_path)
            print(f"Created: {dir_path}")
        else:
            skipped.append(dir_path)
            # print(f"Exists: {dir_path}")

    if created:
        print(f"\nSuccessfully created {len(created)} directories.")
    if skipped:
        print(f"Skipped {len(skipped)} existing directories.")

    return len(created) + len(skipped) == len(REQUIRED_DIRS)

def verify_structure():
    """Verify all required directories exist."""
    root = os.getcwd()
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = os.path.join(root, dir_path)
        if not os.path.isdir(full_path):
            missing.append(dir_path)

    if missing:
        print(f"Verification FAILED. Missing directories: {missing}")
        return False
    else:
        print("Verification PASSED. All required directories exist.")
        return True

def main():
    """Main entry point."""
    print("Initializing llmXive project structure...")
    if not create_directories():
        sys.exit(1)
    
    print("\nVerifying structure...")
    if not verify_structure():
        sys.exit(1)
    
    print("\nProject structure initialization complete.")

if __name__ == "__main__":
    main()
