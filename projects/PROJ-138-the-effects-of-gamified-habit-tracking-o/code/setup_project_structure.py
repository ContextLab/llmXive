"""
Script to initialize the project directory structure for llmXive research pipeline.
Creates required directories and .gitkeep files to ensure they are tracked by git.
"""
import os
import sys

def create_directories():
    """Create the required project directory structure."""
    # Define relative paths based on project requirements
    # Paths are relative to the repository root
    directories = [
        "code/data",
        "code/analysis",
        "code/reports",
        "code/utils",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/consent"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        if os.path.exists(dir_path):
            existing_count += 1
            print(f"Directory exists: {dir_path}")
        else:
            os.makedirs(dir_path, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")

        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write("# Keep this directory tracked by git\n")
            print(f"Created .gitkeep: {gitkeep_path}")
        else:
            print(f".gitkeep already exists: {gitkeep_path}")

    return created_count, existing_count

def verify_structure():
    """Verify all required directories exist."""
    required_dirs = [
        "code/data",
        "code/analysis",
        "code/reports",
        "code/utils",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/consent"
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"ERROR: Missing directories: {missing_dirs}")
        return False
    return True

def main():
    """Main entry point for the script."""
    print("Starting project structure setup...")
    created, existing = create_directories()
    print(f"\nSummary: Created {created} directories, {existing} already existed.")

    if verify_structure():
        print("Verification successful: All required directories exist.")
        sys.exit(0)
    else:
        print("Verification failed: Some directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
