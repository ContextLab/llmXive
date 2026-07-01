import os
import sys

def main():
    """
    Creates the project directory tree for PROJ-234-assessing-statistical-power-in-reproduci
    and verifies that each directory exists.
    """
    project_root = "projects/PROJ-234-assessing-statistical-power-in-reproduci"
    
    # Define the required directories relative to the project root
    # Using absolute paths based on the task description relative to the project root
    # The task asks for paths like `projects/PROJ-234...`
    
    # We will create them relative to the current working directory
    # ensuring the full path structure is created.
    
    directories = [
        f"{project_root}/code/utils",
        f"{project_root}/data/raw",
        f"{project_root}/data/processed",
        f"{project_root}/tests/unit",
        f"{project_root}/tests/contract",
        f"{project_root}/docs",
        f"{project_root}/contracts"
    ]
    
    created_count = 0
    verified_count = 0
    errors = []

    print(f"Creating project directory tree for: {project_root}")

    for dir_path in directories:
        try:
            # Create directory and parents if they don't exist
            os.makedirs(dir_path, exist_ok=True)
            created_count += 1
            print(f"  Created: {dir_path}")
        except OSError as e:
            errors.append(f"Error creating {dir_path}: {e}")
            print(f"  ERROR: Failed to create {dir_path}")

    print(f"\nCreated {created_count} directories.")

    # Verification step: test -d <dir> && echo OK
    print("\nVerifying directory existence:")
    all_verified = True
    for dir_path in directories:
        if os.path.isdir(dir_path):
            print(f"  OK: {dir_path}")
            verified_count += 1
        else:
            print(f"  FAILED: {dir_path} does not exist!")
            all_verified = False

    if all_verified:
        print(f"\nVerification successful: All {verified_count} directories exist.")
        return 0
    else:
        print(f"\nVerification failed: Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())