import os
import sys

def create_project_structure():
    """
    Creates the required subdirectories for the llmXive project.
    Does NOT create the root project directory itself.
    """
    directories = [
        "data/raw",
        "data/results",
        "code",
        "tests/unit",
        "tests/contract",
        "contracts"
    ]

    created = []
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    return created

def main():
    """Entry point for directory setup."""
    print("Setting up project directory structure...")
    created_dirs = create_project_structure()
    if created_dirs:
        print(f"Successfully created {len(created_dirs)} directories.")
    else:
        print("No new directories were created (all already exist).")
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()