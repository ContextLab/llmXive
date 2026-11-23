import os
import sys

def create_project_structure():
    """
    Creates the required subdirectories for the llmXive project.
    Directories created relative to the current working directory (project root).
    """
    # Define the directories to create based on T001 requirements
    directories = [
        "data/raw",
        "data/results",
        "code",
        "tests/unit",
        "tests/contract",
        "contracts"
    ]

    created_count = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    return created_count

def main():
    """
    Entry point for directory setup script.
    """
    print("Setting up project directory structure...")
    created = create_project_structure()
    print(f"Setup complete. Created {created} new directories.")
    
    # Verify structure by listing created dirs
    print("\nVerifying directory structure:")
    for dir_path in ["data/raw", "data/results", "code", "tests/unit", "tests/contract", "contracts"]:
        if os.path.isdir(dir_path):
            print(f"  [OK] {dir_path}/")
        else:
            print(f"  [FAIL] {dir_path}/ (missing)")
            sys.exit(1)

if __name__ == "__main__":
    main()
