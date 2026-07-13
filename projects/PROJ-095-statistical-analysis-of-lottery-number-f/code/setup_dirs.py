import os
import sys

def main():
    """
    Creates the required project directory structure for the Lottery Draw Integrity project.
    This script ensures all necessary folders exist for data storage, code organization,
    and test suites.
    """
    base_dir = os.getcwd()
    
    # Define relative paths as per task T001a
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "config"
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        try:
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                # Optional: check if it is a directory to ensure integrity
                if os.path.isdir(full_path):
                    print(f"Directory already exists: {full_path}")
                    skipped_count += 1
                else:
                    print(f"WARNING: Path exists but is not a directory: {full_path}")
        except PermissionError:
            print(f"ERROR: Permission denied creating {full_path}")
            sys.exit(1)
        except OSError as e:
            print(f"ERROR: Failed to create {full_path}: {e}")
            sys.exit(1)

    print(f"\nSetup complete. Created: {created_count}, Existed: {skipped_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
