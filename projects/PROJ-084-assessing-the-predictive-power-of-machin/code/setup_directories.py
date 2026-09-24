import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    Implements task T001a.
    """
    # Define the base paths relative to the project root
    # We assume the script is run from the project root or code directory.
    # Using Path.cwd() ensures we operate from the current working directory.
    base = Path.cwd()

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]

    created_count = 0
    for dir_name in directories:
        full_path = base / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Directory setup complete. {created_count} new directories created.")

    # Verify existence by listing
    print("\nVerification (ls -R equivalent):")
    for dir_name in directories:
        full_path = base / dir_name
        if full_path.exists():
            # List contents if not empty, otherwise just show the directory
            try:
                contents = list(full_path.iterdir())
                if contents:
                    print(f"{dir_name}/: {', '.join([p.name for p in contents])}")
                else:
                    print(f"{dir_name}/: (empty)")
            except PermissionError:
                print(f"{dir_name}/: (permission denied)")

if __name__ == "__main__":
    main()