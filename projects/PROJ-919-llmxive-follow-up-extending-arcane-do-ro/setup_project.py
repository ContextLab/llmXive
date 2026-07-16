"""
Setup script to initialize the llmXive project structure.
Creates necessary directories for source code, tests, data, and specifications.
"""
import os
import sys

def create_directories():
    """Create the project directory structure."""
    base_dirs = [
        "src",
        "tests",
        "data",
        "specs/001-gene-regulation"
    ]

    # Subdirectories for data as per Phase 2 (T004) anticipation
    data_subdirs = [
        "data/raw",
        "data/derived",
        "data/gold_standard",
        "artifacts"
    ]

    # Subdirectories for specs
    spec_subdirs = [
        "specs/001-gene-regulation/contracts"
    ]

    all_dirs = base_dirs + data_subdirs + spec_subdirs

    created = []
    for dir_path in all_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    return created

def create_gitkeep():
    """Create .gitkeep files in empty directories to ensure they are tracked."""
    dirs_to_keep = [
        "src",
        "tests",
        "data/raw",
        "data/derived",
        "data/gold_standard",
        "artifacts",
        "specs/001-gene-regulation/contracts"
    ]

    for dir_path in dirs_to_keep:
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write("# Keep directory")
            print(f"Created .gitkeep in {dir_path}")

def main():
    print("Initializing llmXive project structure...")
    try:
        create_directories()
        create_gitkeep()
        print("Project structure initialization complete.")
    except Exception as e:
        print(f"Error during initialization: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
