import os
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in T001.
    Ensures all required directories exist.
    """
    # Define the project root (assuming this script is run from project root or code/)
    # We use the parent of this file's directory if run from code/, else current dir
    current_file = Path(__file__)
    project_root = current_file.parent.parent if current_file.name == 'setup_structure.py' else current_file.parent

    # Define required directories relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "state",
        "results/figures"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    # Create .gitkeep files to ensure directories are tracked in git
    # This satisfies the requirement to "show these directories (with at least placeholder files)"
    keep_files = []
    for dir_path in directories:
        full_path = project_root / dir_path
        keep_file = full_path / ".gitkeep"
        if not keep_file.exists():
            keep_file.write_text("")
            keep_files.append(str(keep_file))

    print(f"\nProject structure setup complete.")
    print(f"Directories created: {created_count}")
    print(f"Placeholder files created: {len(keep_files)}")

    # Return the list of created paths for verification if needed
    return [str(project_root / d) for d in directories]

if __name__ == "__main__":
    main()
