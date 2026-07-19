"""
Script to initialize .gitkeep files in all empty project directories.
Ensures version control tracks directory structure even when empty.
"""
import os
import sys

def initialize_gitkeeps():
    """
    Creates .gitkeep files in all specified project directories.
    Returns a list of created file paths.
    """
    # Define the root directories relative to the project root
    # Based on T001b requirements: code/, data/, data/raw/, data/processed/,
    # data/visualizations/, tests/, tests/unit/, tests/integration/, docs/
    base_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/visualizations",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_files = []
    errors = []

    for dir_path in base_dirs:
        # Ensure the directory exists first
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except OSError as e:
                errors.append(f"Failed to create directory {dir_path}: {e}")
                continue

        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        
        # Create .gitkeep only if it doesn't exist
        if not os.path.exists(gitkeep_path):
            try:
                with open(gitkeep_path, 'w') as f:
                    f.write("# Keep this file to preserve directory structure in git\n")
                created_files.append(gitkeep_path)
            except IOError as e:
                errors.append(f"Failed to create .gitkeep in {dir_path}: {e}")
        else:
            # .gitkeep already exists
            created_files.append(gitkeep_path)

    if errors:
        print("Errors occurred during .gitkeep initialization:")
        for error in errors:
            print(f"  - {error}")
        return False, created_files, errors

    print(f"Successfully initialized {len(created_files)} .gitkeep files:")
    for f in created_files:
        print(f"  - {f}")
    
    return True, created_files, []

def main():
    """Main entry point for the script."""
    print("Initializing .gitkeep files in project directories...")
    success, created, errors = initialize_gitkeeps()
    
    if success:
        print("\nInitialization complete.")
        sys.exit(0)
    else:
        print("\nInitialization completed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()